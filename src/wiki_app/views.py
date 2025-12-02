from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import process_repository_task
from .models import Repository, Branch, Folder, File
import time
import json

FILE_RETURN_LIMIT = 600

def index(request):
    return render(request, 'index.html')

def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('index')
    
    # Normalize input
    # Remove trailing slash and .git
    query = query.rstrip('/')
    if query.endswith('.git'):
        query = query[:-4]

    # Extract owner/repo
    if 'github.com/' in query:
        # Works for https://github.com/owner/repo and github.com/owner/repo
        path = query.split('github.com/')[-1]
        parts = path.split('/')
    else:
        parts = query.split('/')

    # Filter out empty strings
    parts = [p for p in parts if p]

    if len(parts) < 2:
         return render(request, 'index.html', {'error': 'Invalid format. Please use owner/repo or a GitHub URL'})
    
    owner = parts[0]
    repo = parts[1]
    
    # Check if exists
    if Repository.objects.filter(owner=owner, repo=repo).exists():
        return redirect('repo_detail', owner=owner, repo=repo)
    
    # Create placeholder for queue tracking
    Repository.objects.create(
        url=f"https://github.com/{owner}/{repo}",
        owner=owner,
        repo=repo,
        default_branch='main',
        process_status='Queued'
    )

    # Trigger task
    task = process_repository_task.delay(owner, repo)
    
    return render(request, 'processing.html', {
        'owner': owner,
        'repo': repo,
        'task_id': task.id
    })

def repo_detail(request, owner, repo):
    repository = get_object_or_404(Repository, owner=owner, repo=repo)
    
    # Get the latest branch
    branch = repository.branches.order_by('-created_at').first()
    
    # Check if processing is complete (i.e., summary exists)
    if not branch or not branch.ai_summary:
        # If not ready, render processing page
        return render(request, 'processing.html', {
            'owner': owner,
            'repo': repo,
            'task_id': None # We don't have task ID here easily, but that's fine for polling
        })
    
    file_qs = File.objects.filter(folder__branch=branch)
    # Only inspect a small sample to decide if we should include files; avoid loading large file sets
    sampled_ids = list(file_qs.values_list('file_id', flat=True)[: FILE_RETURN_LIMIT + 1])
    include_files = len(sampled_ids) <= FILE_RETURN_LIMIT
    total_files = len(sampled_ids) if include_files else None

    # Build file tree
    file_tree = build_tree(branch, include_files=include_files)
    
    return render(request, 'repo.html', {
        'repository': repository,
        'branch': branch,
        'file_tree': file_tree,
        'files_omitted': not include_files,
        'total_files': total_files,
        'file_return_limit': FILE_RETURN_LIMIT
    })

def build_tree(branch, include_files=True):
    folders = Folder.objects.filter(branch=branch).select_related('parent_folder')
    files = File.objects.none()
    if include_files:
        files = File.objects.filter(folder__branch=branch).select_related('folder')
    
    # Map folder_id -> node
    folder_nodes = {}
    for f in folders:
        folder_nodes[f.folder_id] = {
            'type': 'folder',
            'obj': f,
            'children': [], # List of folder nodes or file nodes
            'is_root': f.path == ""
        }
        
    # Add files to folder nodes
    for f in files:
        if f.folder_id in folder_nodes:
            folder_nodes[f.folder_id]['children'].append({
                'type': 'file',
                'obj': f
            })
            
    # Build hierarchy
    roots = []
    for f in folders:
        node = folder_nodes[f.folder_id]
        if f.parent_folder_id:
            parent = folder_nodes.get(f.parent_folder_id)
            if parent:
                parent['children'].append(node)
            else:
                roots.append(node) # Orphaned? Treat as root
        else:
            roots.append(node)
            
    # If we have a root folder (path=""), we want to return it as the top level
    # instead of flattening it.
    # And rename it to "/"
    for node in roots:
        if node['is_root']:
            node['obj'].name = "/"
            
    # Sort children by name (folders first?)
    def sort_node(node):
        if node['type'] == 'folder':
            node['children'].sort(key=lambda x: (x['type'] != 'folder', x['obj'].name))
            for child in node['children']:
                sort_node(child)
                
    for node in roots:
        sort_node(node)
        
    roots.sort(key=lambda x: (x['type'] != 'folder', x['obj'].name))
    
    return roots

def repo_status_stream(request, owner, repo):
    def event_stream():
        timeout_counter = 0
        max_retries_for_creation = 30 # Wait 60 seconds for the repo to be created
        last_message = None

        while True:
            # Check if repository is processed
            try:
                # Force fresh read from DB (avoid cached results)
                from django.db import connection
                connection.close()
                repository = Repository.objects.get(owner=owner, repo=repo)
                branch = repository.branches.order_by('-created_at').first()
                
                if branch and branch.ai_summary:
                    # Send completion event
                    data = json.dumps({'status': 'complete'})
                    yield f"data: {data}\n\n"
                    break
                else:
                    # Send processing event with status message and start time
                    status_msg = repository.process_status or "Processing..."
                    start_time = repository.process_start_at.isoformat() if repository.process_start_at else None
                    
                    # Calculate queue position if status is 'Queued'
                    queue_pos = None
                    if status_msg == 'Queued':
                        queue_pos = Repository.objects.filter(
                            process_status='Queued', 
                            queued_at__lt=repository.queued_at
                        ).count() + 1

                    # Only send if message changed to reduce noise, or always send for timer sync
                    data = json.dumps({
                        'status': 'processing', 
                        'message': status_msg,
                        'start_time': start_time,
                        'queue_pos': queue_pos
                    })
                    yield f"data: {data}\n\n"
            except Repository.DoesNotExist:
                if timeout_counter > max_retries_for_creation:
                     data = json.dumps({'status': 'error', 'message': 'Repository initialization timed out or failed.'})
                     yield f"data: {data}\n\n"
                     break

                data = json.dumps({'status': 'processing', 'message': 'Initializing repository...'})
                yield f"data: {data}\n\n"
                timeout_counter += 1
            
            time.sleep(1) # Check every 1 second for more responsive updates

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in Nginx
    return response

class RepositoryQueueView(APIView):
    def get(self, request):
        # For now, return empty queue status as we moved to Celery
        # We could implement Celery inspection here if needed
        return Response({
            "current": None,
            "queue": [],
            "time": None
        })

    def post(self, request):
        owner = request.data.get('owner')
        repo = request.data.get('repo')
        if not owner or not repo:
            return Response({"success": False, "message": "Owner and repo required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if exists
        if Repository.objects.filter(owner=owner, repo=repo).exists():
             return Response({"success": False, "message": "Item already in database"}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger task
        task = process_repository_task.delay(owner, repo)
        return Response({
            "success": True,
            "message": f"Repository {owner}/{repo} added to queue",
            "task_id": task.id
        }, status=status.HTTP_201_CREATED)
