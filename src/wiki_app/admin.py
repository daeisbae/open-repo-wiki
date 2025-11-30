from django.contrib import admin

from .models import Branch, File, Folder, Repository, Topic


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("owner", "repo", "language", "stars", "forks", "process_status", "process_start_at")
    search_fields = ("owner", "repo", "url")
    list_filter = ("language",)
    date_hierarchy = "process_start_at"
    ordering = ("owner", "repo")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "repository", "last_commit_sha", "commit_at", "created_at")
    search_fields = ("name", "repository__owner", "repository__repo", "last_commit_sha")
    list_filter = ("name",)
    ordering = ("-created_at",)
    list_select_related = ("repository",)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "branch", "parent_folder")
    search_fields = ("name", "path", "branch__repository__owner", "branch__repository__repo")
    list_filter = ("branch",)
    ordering = ("path",)
    list_select_related = ("branch", "parent_folder")


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "folder", "language")
    search_fields = ("name", "folder__path", "folder__branch__repository__owner", "folder__branch__repository__repo")
    list_filter = ("language",)
    ordering = ("name",)
    list_select_related = ("folder", "folder__branch", "folder__branch__repository")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ("topic_name",)
