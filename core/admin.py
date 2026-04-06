from django.contrib import admin
from core.models import Mentor, Student, Project, ProjectStage

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'phone')
    search_fields = ('user__last_name', 'user__first_name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'group_name', 'mentor')
    search_fields = ('last_name', 'first_name')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'student', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name',)

@admin.register(ProjectStage)
class ProjectStageAdmin(admin.ModelAdmin):
    list_display = ('project', 'stage_name', 'planned_date', 'is_completed')
    list_filter = ('is_completed', 'planned_date')