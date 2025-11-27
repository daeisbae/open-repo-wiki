from django.db import models

class Topic(models.Model):
    topic_name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        db_table = 'topics'

class Repository(models.Model):
    url = models.CharField(max_length=255, primary_key=True)
    owner = models.CharField(max_length=255)
    repo = models.CharField(max_length=255)
    language = models.CharField(max_length=100, null=True, blank=True)
    descriptions = models.TextField(null=True, blank=True)
    default_branch = models.CharField(max_length=255)
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    topics = models.ManyToManyField(Topic, related_name='repositories', db_table='repository_topics')

    # Status tracking
    process_status = models.TextField(default="Initializing...")
    process_start_at = models.DateTimeField(auto_now_add=True, null=True)
    queued_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'repository'

class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    last_commit_sha = models.CharField(max_length=255)
    commit_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    ai_summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'branch'
        unique_together = ('repository', 'last_commit_sha')

class Folder(models.Model):
    folder_id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    name = models.CharField(max_length=255)
    path = models.TextField()
    ai_summary = models.TextField(null=True, blank=True)
    usage = models.TextField(null=True, blank=True)
    dependency_graph = models.TextField(null=True, blank=True)  # Mermaid diagram string

    class Meta:
        db_table = 'folder'

class File(models.Model):
    file_id = models.AutoField(primary_key=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField()
    ai_summary = models.TextField(null=True, blank=True)
    usage = models.TextField(null=True, blank=True)
    dependencies = models.JSONField(null=True, blank=True, default=list)  # List of imported modules

    class Meta:
        db_table = 'file'
