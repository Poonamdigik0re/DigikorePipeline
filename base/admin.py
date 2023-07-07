from django.contrib import admin

from base.forms import *
from base.models import *


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'gid')
    list_display = ('name', 'total_users', 'gid')
    ordering = ('gid',)

    def total_users(self, location):
        return UserProfile.objects.filter(location=location, user__is_active=True).count()


@admin.register(LdapGroup)
class LdapGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_users', 'gid')
    fields = ('name',)
    ordering = ('gid',)

    def total_users(self, ldap_group):
        return UserProfile.objects.filter(designation__ldap_group=ldap_group, user__is_active=True).count()


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'ldap_group', 'site_group', 'is_artist')
    fields = ('name', 'ldap_group', 'site_group', 'is_artist')
    ordering = ('ldap_group', 'site_group', 'name')
    list_filter = ('ldap_group', 'site_group', 'is_artist')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_planner', 'order')
    fields = ('name', 'resource_planner', 'order')
    list_filter = ('resource_planner',)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    fields = ('name', 'intime', 'outtime', 'color')
    list_display = ('name', 'intime', 'outtime', 'color')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    fields = ('name',)


@admin.register(CompanyHoliday)
class CompanyHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'working')
    fields = ('name', 'date', 'working')


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'default', 'locked')
    fields = ('name', 'order', 'default', 'locked')

    def save_model(self, request, obj, form, change):
        if change:
            old_value = ProjectStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='project', key='status', value=old_value).update(value=obj.name)

        super(ProjectStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default')
    fields = ('name', 'default')

    def save_model(self, request, obj, form, change):
        if change:
            old_value = ProjectType.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='project', key='type', value=old_value).update(value=obj.name)

        super(ProjectTypeAdmin, self).save_model(request, obj, form, change)


@admin.register(ShotStatus)
class ShotStatusAdmin(admin.ModelAdmin):
    form = ShotStatusForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = ShotStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='shot', key='status', value=old_value).update(value=obj.name)

        super(ShotStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'order', 'default')
    fields = ('name', 'department', 'order', 'default')
    ordering = ('order',)

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TaskType.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='task', key='type', value=old_value).update(value=obj.name)

        super(TaskTypeAdmin, self).save_model(request, obj, form, change)


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    form = TaskStatusForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (
                ('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TaskStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='task', key='status', value=old_value).update(value=obj.name)

        super(TaskStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(TaskComplexity)
class TaskComplexityAdmin(admin.ModelAdmin):
    form = TaskComplexityForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TaskComplexity.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='task', key='complexity', value=old_value).update(value=obj.name)

        super(TaskComplexityAdmin, self).save_model(request, obj, form, change)


@admin.register(TaskPriority)
class TaskPriorityAdmin(admin.ModelAdmin):
    form = TaskPriorityForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TaskPriority.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='task', key='priority', value=old_value).update(value=obj.name)

        super(TaskPriorityAdmin, self).save_model(request, obj, form, change)


@admin.register(SubtaskStatus)
class SubtaskStatusAdmin(admin.ModelAdmin):
    form = SubtaskStatusForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (
                ('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = SubtaskStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='subtask', key='status', value=old_value).update(value=obj.name)

        super(SubtaskStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(FilerecordType)
class FilerecordTypeAdmin(admin.ModelAdmin):
    fields = ('name',)

    def save_model(self, request, obj, form, change):
        if change:
            old_value = FilerecordType.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='filerecord', key='type', value=old_value).update(value=obj.name)

        super(FilerecordTypeAdmin, self).save_model(request, obj, form, change)


@admin.register(FilerecordStatus)
class FilerecordStatusAdmin(admin.ModelAdmin):
    form = FilerecordStatusForm
    list_display = ['colored_name', 'default']
    fieldsets = (
        (None, {
            'fields': (
                ('name', 'default'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = FilerecordStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='filerecord', key='status', value=old_value).update(value=obj.name)

        super(FilerecordStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(NoteType)
class NoteTypeAdmin(admin.ModelAdmin):
    form = NoteTypeForm
    list_display = ['colored_name', 'default', 'order']
    fieldsets = (
        (None, {
            'fields': (('name', 'default', 'order'), 'bg_color', 'fg_color')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_value = NoteType.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='note', key='type', value=old_value).update(value=obj.name)

        super(NoteTypeAdmin, self).save_model(request, obj, form, change)


@admin.register(BidStatus)
class BidStatusAdmin(admin.ModelAdmin):
    form = BidStatusForm
    list_display = ('name', 'default', 'locked')
    fields = ('name', 'default', 'locked', 'bg_color', 'fg_color')

    def save_model(self, request, obj, form, change):
        if change:
            old_value = BidStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='bid', key='status', value=old_value).update(value=obj.name)

        super(BidStatusAdmin, self).save_model(request, obj, form, change)


@admin.register(EmailGroup)
class EmailGroupAdmin(admin.ModelAdmin):
    fields = ('name', 'mail_to', 'cc_to')


@admin.register(BaseRate)
class BaseRateAdmin(admin.ModelAdmin):
    fields = ('task_type', 'rate')
    list_display = ('task_type', 'rate')


@admin.register(BaseROP)
class BaseROPAdmin(admin.ModelAdmin):
    fields = ('task_type', 'rate')
    list_display = ('task_type', 'rate')


@admin.register(TicketPriority)
class TicketPriorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'order')
    fields = ('name', 'default', 'order')
    ordering = ('order',)

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TicketPriority.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='ticket', key='type', value=old_value).update(value=obj.name)

        super(TicketPriorityAdmin, self).save_model(request, obj, form, change)


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'order')
    fields = ('name', 'default', 'order')
    ordering = ('order',)

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TicketType.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='ticket', key='type', value=old_value).update(value=obj.name)

        super(TicketTypeAdmin, self).save_model(request, obj, form, change)


@admin.register(TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'order', 'locked')
    fields = ('name', 'default', 'order', 'locked')
    ordering = ('order',)

    def save_model(self, request, obj, form, change):
        if change:
            old_value = TicketStatus.objects.get(id=obj.id).name
            ChangeLog.objects.filter(parent_type='ticket', key='type', value=old_value).update(value=obj.name)

        super(TicketStatusAdmin, self).save_model(request, obj, form, change)
