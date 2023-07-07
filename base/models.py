import os
from uuid import uuid4

from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.html import format_html

from DigikorePortal.settings import CONFIG

USERPROFILE_CONFIRMATION_CHOICES = (('pending', 'Pending'),
                                    ('confirmed', 'Confirmed'),
                                    ('terminated', 'Terminated'),
                                    ('notice_period', 'Service Notice Period'),
                                    ('resigned', 'Resigned'),
                                    ('absconding', 'Absconding'))


def upload_attachment(instance, filename):
    _, ext = os.path.splitext(filename)
    name = uuid4()

    return f'attachments/{name}{ext}'


class AppPermissions(models.Model):
    class Meta:
        default_permissions = []
        permissions = (
            # Home
            ('add_announcement', 'add_announcement'),

            # Employee Manager
            ('employee_manager', 'employee_manager'),
            ('employee_manager_manager', 'employee_manager_manager'),
            ('employee_manager_admin', 'employee_manager_admin'),

            # Attendance
            ('attendance', 'attendance'),
            ('attendance_readonly', 'attendance_readonly'),
            ('attendance_admin', 'attendance_admin'),
            ('attendance_prod_view', 'attendance_prod_view'),

            # Leave manager
            ('leave_manager', 'leave_manager'),
            ('leave_manager_lead', 'leave_manager_lead'),
            ('leave_manager_manager', 'leave_manager_manager'),
            ('leave_manager_admin', 'leave_manager_admin'),

            # Team Manager
            ('team_manager', 'team_manager'),
            ('team_manager_admin', 'team_manager_admin'),
            ('team_manager_manager', 'team_manager_manager'),

            # Clients List
            ('clients_list', 'clients_list'),

            # Vendors List
            ('vendors_list', 'vendors_list'),

            # Projects List
            ('projects_list', 'projects_list'),
            ('projects_list_add_project', 'projects_list_add_project'),

            # Project Overview
            ('projects_overview', 'projects_overview'),

            # Projects List
            ('projects_permission', 'projects_permission'),

            # Projects List
            ('projects', 'projects'),

            # Task Overview
            ('task_overview', 'task_overview'),
            ('task_overview_add_subtask', 'task_overview_add_subtask'),

            # Resource Planner
            ('resource_planner', 'resource_planner'),
            ('resource_planner_update', 'resource_planner_update'),

            # Ingest System
            ('ingest_system', 'ingest_system'),

            # Bidding System
            ('bidding_system', 'bidding_system'),
            ('bidding_system_bid_rate', 'bidding_system_bid_rate'),

            # Site Sync
            ('site_sync', 'site_sync'),

            # Tasks list
            ('tasks_list', 'tasks_list'),

            # Shots list
            ('shots_list', 'shots_list'),

            # Check artist utilization
            ('artist_utilization', 'artist_utilization'),

            # Workstation
            ('workstations', 'workstations'),

            # Workstation
            ('file_transfer', 'file_transfer'),

            # Project Archival
            ('project_archival', 'project_archival'),

            # Transportation
            ('transportation_page', 'transportation_page'),

            # Vehicle Directory
            ('vehicle_directory', 'vehicle_directory'),

            # Gmail Alias
            ('gmail_group', 'gmail_group'),
            ('create_gmail_group', 'create_gmail_group'),

            # Ticket Page
            ('tickets', 'tickets'),
            ('tickets_maintainer', 'tickets_maintainer'),
            ('tickets_admin', 'tickets_admin'),
        )


class Location(models.Model):
    name = models.CharField(max_length=3, unique=True)
    description = models.CharField(max_length=40, null=True, blank=True)
    gid = models.IntegerField(default=100000, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class LdapGroup(models.Model):
    name = models.CharField(max_length=40, unique=True)
    gid = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.gid = CONFIG['ldap']['group_gid'] + LdapGroup.objects.count() + 1

        super(LdapGroup, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Shift(models.Model):
    # location = models.ForeignKey(Location, related_name='shift_location', on_delete=models.PROTECT)
    name = models.CharField(max_length=40)
    intime = models.TimeField()
    outtime = models.TimeField()
    color = models.CharField(max_length=7, default='#1ec5b6')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Designation(models.Model):
    name = models.CharField(max_length=40, unique=True)
    site_group = models.ForeignKey(Group, related_name='designation_site_group', on_delete=models.PROTECT)
    ldap_group = models.ForeignKey(LdapGroup, related_name='designation_ldap_group', on_delete=models.PROTECT)
    is_artist = models.BooleanField(default=False, help_text='Add this in resource allocation')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Department(models.Model):
    name = models.CharField(max_length=40, unique=True)
    order = models.SmallIntegerField(default=1)
    resource_planner = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Team(models.Model):
    location = models.ForeignKey(Location, related_name='team_location', on_delete=models.PROTECT)
    department = models.ForeignKey(Department, related_name='team_department', on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, related_name='team_shift', on_delete=models.PROTECT)
    lead = models.ForeignKey(User, related_name='team_lead', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []

    def get_some_property(self):
        return self._some_property

    def set_some_property(self, value):
        self._some_property = value

    some_property = property(get_some_property, set_some_property)


class Skill(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        default_permissions = []

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name='userprofile_location', on_delete=models.PROTECT)
    uid = models.IntegerField(default=0)

    full_name = models.CharField(max_length=40, unique=True)
    empid = models.CharField(max_length=40, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='userprofile_department')
    designation = models.ForeignKey(Designation, on_delete=models.PROTECT, related_name='userprofile_designation')
    date_of_joining = models.DateField()

    gender = models.CharField(max_length=10, default='male')
    blood_group = models.CharField(max_length=6, null=True, blank=True)
    date_of_birth = models.DateField()

    category = models.CharField(max_length=40, null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, null=True, blank=True)

    phone = models.TextField(null=True, blank=True)
    current_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)
    emergency_contact = models.TextField(null=True, blank=True)
    emergency_phone = models.CharField(max_length=40, null=True, blank=True)

    confirmation_status = models.CharField(max_length=20, default='pending', choices=USERPROFILE_CONFIRMATION_CHOICES)

    confirmation_date = models.DateField(null=True, blank=True)
    confirmation_letter_issued = models.BooleanField(default=False)
    expected_rop = models.SmallIntegerField(default=0)

    bgv_report = models.CharField(max_length=40, null=True, blank=True)
    bgv_result = models.CharField(max_length=40, null=True, blank=True)

    pip_start_date = models.DateField(null=True, blank=True)
    pip_end_date = models.DateField(null=True, blank=True)

    date_of_leaving = models.DateField(null=True, blank=True)
    reason_of_leaving = models.TextField(null=True, blank=True)

    paid_leave = models.FloatField(default=0)
    casual_leave = models.FloatField(default=0)
    comp_off = models.FloatField(default=0)

    skills = models.ManyToManyField(Skill, related_name='userprofile_skills')
    team = models.ForeignKey(Team, related_name='userprofile_team', on_delete=models.SET_NULL, null=True, blank=True)
    transport_required = models.CharField(max_length=3, default='no')

    vehicle_type = models.CharField(max_length=10, null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, null=True, blank=True)

    profile_picture = models.TextField(default='/static/img/default_profile.png')
    employment_type = models.CharField(max_length=50, null=True, blank=True)

    # Password reset settings
    password_reset = models.BooleanField(default=False)
    password_reset_on = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        default_permissions = []


class Compoff(models.Model):
    user = models.ForeignKey(User, related_name='compoff_user', on_delete=models.PROTECT)
    date = models.DateField()
    total_days = models.FloatField(default=0)
    status = models.CharField(max_length=20, default='pending', choices=(('pending', 'Pending'),
                                                                         ('approved', 'Approved'),
                                                                         ('canceled', 'Canceled'),
                                                                         ('rejected', 'Rejected')))
    reason = models.CharField(max_length=200)
    rejection = models.CharField(max_length=200, null=True, blank=True)

    can_be_incentive = models.BooleanField(default=False)
    is_incentive = models.BooleanField(default=False)

    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, related_name='compoff_updated_by', null=True, blank=True,
                                   on_delete=models.SET_NULL)

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = []


class Leave(models.Model):
    user = models.ForeignKey(User, related_name='leave_user', on_delete=models.PROTECT)
    leave_type = models.CharField(max_length=20, default='paid_leave', choices=(('sick_leave', 'Sick Leave'),
                                                                                ('paid_leave', 'Paid Leave'),
                                                                                ('casual_leave', 'Casual Leave'),
                                                                                ('comp_off', 'Comp Off'),
                                                                                ('unpaid_leave', 'Unpaid Leave')))

    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.FloatField(default=0)
    status = models.CharField(max_length=20, default='pending', choices=(('pending', 'Pending'),
                                                                         ('approved', 'Approved'),
                                                                         ('canceled', 'Canceled'),
                                                                         ('rejected', 'Rejected')))

    reason = models.CharField(max_length=200)
    rejection = models.CharField(max_length=200, null=True, blank=True)

    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, related_name='leave_updated_by', null=True, blank=True,
                                   on_delete=models.SET_NULL)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='leave_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class LeaveLog(models.Model):
    user = models.ForeignKey(User, related_name='leave_log_user', on_delete=models.PROTECT, null=True)
    leave_type = models.CharField(max_length=20, default='paid_leave', choices=(('sick_leave', 'Sick Leave'),
                                                                                ('paid_leave', 'Paid Leave'),
                                                                                ('casual_leave', 'Casual Leave'),
                                                                                ('comp_off', 'Comp Off'),
                                                                                ('unpaid_leave', 'Unpaid Leave')))

    total_days = models.FloatField(default=0)
    comment = models.CharField(max_length=200)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='leave_log_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class Attendance(models.Model):
    user = models.ForeignKey(User, related_name='attendance_user', on_delete=models.PROTECT)
    type = models.CharField(max_length=20, default='IN', choices=(('PR', 'Present'),
                                                                  ('LOP', 'Loss of Pay'),
                                                                  ('IA', 'Informed Absent'),
                                                                  ('LE', 'Leave'),
                                                                  ('HD', 'Half Day'),
                                                                  ('HL', 'Half Day Leave')))

    date = models.DateField()
    intime = models.DateTimeField(null=True)
    outtime = models.DateTimeField(null=True)
    working_hours = models.IntegerField(null=True)

    class Meta:
        default_permissions = []


class CompanyHoliday(models.Model):
    location = models.ForeignKey(Location, related_name='holiday_location', on_delete=models.PROTECT)
    date = models.DateField()
    name = models.CharField(max_length=40)
    working = models.BooleanField(default=False)

    class Meta:
        default_permissions = []

    def __str__(self):
        return self.name


class ReportingRule(models.Model):
    junior = models.ForeignKey(Designation, related_name='reporting_rule_junior', on_delete=models.PROTECT)
    senior = models.ForeignKey(Designation, related_name='reporting_rule_senior', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []

    def __str__(self):
        return f"{self.junionr.name} -> {self.senior.name}"


########################################################################################################################
# PROJECT MODELS
########################################################################################################################

class Contact(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField(max_length=40, unique=True)
    title = models.CharField(max_length=40, null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='contact_created_by', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Vendor(models.Model):
    name = models.CharField(max_length=40, unique=True)
    address = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(Contact, related_name='vendor_contacts')

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='vendor_created_by', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Client(models.Model):
    name = models.CharField(max_length=40, unique=True)
    address = models.TextField(blank=True, null=True)

    contacts = models.ManyToManyField(Contact, related_name='client_contacts')
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='client_created_by', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class ProjectStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=1)
    locked = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ProjectStatus.objects.all().update(default=False)

        super(ProjectStatus, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Project Statuses"


class ProjectType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ProjectType.objects.all().update(default=False)

        super(ProjectType, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Project Types"


class Project(models.Model):
    client = models.ForeignKey(Client, related_name='project_client', on_delete=models.PROTECT)
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField(null=True, blank=True)
    type = models.ForeignKey(ProjectType, related_name='project_type', on_delete=models.PROTECT)
    status = models.ForeignKey(ProjectStatus, related_name='project_status', on_delete=models.PROTECT)
    fps = models.FloatField(default=24)
    gid = models.IntegerField(default=0)

    change_order = models.SmallIntegerField(default=0)
    markup_perc = models.FloatField(default=0)
    markup_value = models.FloatField(default=0)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    contacts = models.ManyToManyField(Contact, related_name='project_contacts')
    vendors = models.ManyToManyField(Vendor, related_name='project_vendors')
    default_tasks = models.ManyToManyField('TaskType')

    users = models.ManyToManyField(User, related_name='project_users')
    producers = models.ManyToManyField(User, related_name='project_producers')
    department = models.ManyToManyField(Department, related_name='project_department')
    production = models.ManyToManyField(User, related_name='project_production')
    supervisors = models.ManyToManyField(User, related_name='project_supervisors')

    client_emails = models.TextField(null=True)
    internal_emails = models.TextField(null=True)
    vault_url = models.URLField(null=True)

    thumbnail = models.TextField(default='/static/img/default_poster.png')
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='project_created_by', on_delete=models.PROTECT)

    # Archival fields
    archive_size = models.CharField(max_length=20, default=0)
    archive_percent = models.SmallIntegerField(default=0)

    archive_ready_on = models.DateTimeField(null=True, blank=True)
    archive_ready_by = models.ForeignKey(User, related_name='project_archive_ready_by', on_delete=models.SET_NULL,
                                         null=True)
    archive_started_on = models.DateTimeField(null=True, blank=True)
    archive_started_by = models.ForeignKey(User, related_name='project_archive_started_by', on_delete=models.SET_NULL,
                                           null=True)
    archive_completed_on = models.DateTimeField(null=True, blank=True)

    # temp fields
    msi_sync = models.BooleanField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.gid = 1

        super(Project, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class ShotStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ShotStatus.objects.all().update(default=False)

        super(ShotStatus, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []
        verbose_name_plural = "Shot Statuses"


class Shot(models.Model):
    project = models.ForeignKey(Project, related_name='shot_project', on_delete=models.PROTECT)
    sequence = models.CharField(max_length=40, null=True, blank=True)
    scene = models.CharField(max_length=40, null=True, blank=True)
    reel = models.CharField(max_length=40, null=True, blank=True)
    episode = models.CharField(max_length=40, null=True, blank=True)
    name = models.CharField(max_length=40, default='Shot')

    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()

    status = models.ForeignKey(ShotStatus, related_name='shot_status', on_delete=models.PROTECT)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    client_first_frame = models.IntegerField(default=0)
    client_last_frame = models.IntegerField(default=0)
    working_first_frame = models.IntegerField(default=0)
    working_last_frame = models.IntegerField(default=0)

    # temp fields
    msi_record_code = models.CharField(max_length=40, null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='shot_change_order_created_by', on_delete=models.PROTECT)

    # new fields
    department = models.ManyToManyField(Department, related_name='shot_department')
    # new fields
    show_name = models.CharField(max_length=40, null=True)
    description = models.TextField(null=True, blank=True)
    fps = models.FloatField(default=24)
    resolution = models.CharField(max_length=100, null=True, blank=True)
    thumbnail = models.TextField(default='/static/img/default_poster.png')
    vault_url = models.URLField(null=True)
    annotation = models.TextField(default='/static/img/default_poster.png')
    client_remarks = models.TextField(max_length=200, null=True)
    internal_supervisor_remarks = models.TextField(max_length=200, null=True)
    client_feedback = models.TextField(max_length=250, null=True)
    bids = models.FloatField(default=0)
    execution_type = models.CharField(max_length=250, null=True)
    internal_approval = models.ForeignKey(UserProfile, to_field='full_name', related_name='employee_position',
                                          on_delete=models.PROTECT, null=True)

    def delete(self, *args, **kwargs):
        Note.objects.filter(parent_type='task', parent_id=self.id).delete()
        ChangeLog.objects.filter(parent_type='task', parent_id=self.id).delete()
        Attachment.objects.filter(parent_type='task', parent_id=self.id).delete()

        super(Shot, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class ChangeOrder(models.Model):
    project = models.ForeignKey(Project, related_name='change_order_project', on_delete=models.PROTECT)
    shot = models.ForeignKey(Shot, related_name='change_order_shot', on_delete=models.PROTECT)

    description = models.TextField(null=True, blank=True)
    methodology = models.TextField(null=True, blank=True)
    assumption = models.TextField(null=True, blank=True)

    client_bid_note = models.TextField(null=True, blank=True)
    digikore_bid_note = models.TextField(null=True, blank=True)

    bid_status = models.CharField(max_length=10, default='growth',
                                  choices=(('growth', 'growth'), ('bidding', 'bidding'), ('awarded', 'awarded')))
    bid_id = models.CharField(max_length=40, null=True, blank=True)
    turnover = models.SmallIntegerField(default=1)
    change_order = models.SmallIntegerField(default=0)

    turnover_date = models.DateField(null=True, blank=True)

    bid_cost = models.FloatField(default=0)  # total cost of all bids * rates
    markup_perc = models.FloatField(default=0)
    markup_value = models.FloatField(default=0)
    cost_to_date_perc = models.FloatField(default=0)
    cost_to_date_value = models.FloatField(default=0)

    client_first_frame = models.IntegerField(default=0)
    client_last_frame = models.IntegerField(default=0)

    working_first_frame = models.IntegerField(default=0)
    working_last_frame = models.IntegerField(default=0)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='change_order_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class ChangeOrderBid(models.Model):
    project = models.ForeignKey(Project, related_name='change_order_bid_project', on_delete=models.PROTECT)
    shot = models.ForeignKey(Shot, related_name='change_order_bid_shot', on_delete=models.PROTECT)
    change_order = models.ForeignKey(ChangeOrder, related_name='change_order_bid_co', on_delete=models.PROTECT)
    task_type = models.ForeignKey('TaskType', related_name='change_order_bid_task_type', on_delete=models.PROTECT)
    bid = models.FloatField(default=0)
    rate = models.FloatField(default=0)

    class Meta:
        default_permissions = []


class TaskType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    order = models.SmallIntegerField(default=1, help_text="Sort Order")
    default = models.BooleanField(default=False)
    # connect task type to department for resource planner
    department = models.ForeignKey(Department, related_name='tasktype_department', on_delete=models.PROTECT)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            TaskType.objects.all().update(default=False)

        super(TaskType, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Task Types"


class TaskStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            TaskStatus.objects.all().update(default=False)

        super(TaskStatus, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []
        verbose_name_plural = "Task Statuses"


class TaskComplexity(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            TaskComplexity.objects.all().update(default=False)

        super(TaskComplexity, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []
        verbose_name_plural = "Task Complexities"


class TaskPriority(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            TaskPriority.objects.all().update(default=False)

        super(TaskPriority, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []
        verbose_name_plural = "Task Priorities"


class Task(models.Model):
    project = models.ForeignKey(Project, related_name='task_project', on_delete=models.PROTECT)
    parent_type = models.CharField(null=True, max_length=20)
    parent_id = models.IntegerField(null=True)

    name = models.CharField(max_length=40, default='main')
    type = models.ForeignKey(TaskType, related_name='task_type', on_delete=models.PROTECT)
    status = models.ForeignKey(TaskStatus, related_name='task_status', on_delete=models.PROTECT)
    complexity = models.ForeignKey(TaskComplexity, related_name='task_complexity',null=True, blank=True, on_delete=models.PROTECT)
    priority = models.ForeignKey(TaskPriority, related_name='task_priority', on_delete=models.PROTECT)

    assignee = models.ForeignKey(User, related_name='task_assignee', null=True, blank=True, on_delete=models.SET_NULL)
    vendor = models.ForeignKey(Vendor, related_name='task_vendor', null=True, blank=True, on_delete=models.SET_NULL)

    description = models.TextField(null=True, blank=True)
    bids = models.FloatField(default=0)
    actuals = models.IntegerField(default=0)  # this sums up from subtasks

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    turnover_date = models.DateField(null=True, blank=True)

    working_first_frame = models.IntegerField(default=0)
    working_last_frame = models.IntegerField(default=0)

    # this is temporary
    approved_version = models.IntegerField(default=0)
    # msi_record_code = models.CharField(max_length=40, null=True, blank=True)

    # new fields
    delivered_version = models.IntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)
    start_frame = models.IntegerField(default=0)
    turnover_no = models.IntegerField(default=0)
    end_frame = models.IntegerField(default=0)
    assign_bid = models.IntegerField(default=0)
    scope_of_work = models.TextField(null=True, blank=True)
    shot = models.ForeignKey(Shot, related_name='task_shot', on_delete=models.PROTECT)
    department = models.ForeignKey(Department, related_name='task_department', on_delete=models.PROTECT)
    thumbnail = models.TextField(default='/static/img/default_poster.png')

    def delete(self, *args, **kwargs):
        Note.objects.filter(parent_type='task', parent_id=self.id).delete()
        ChangeLog.objects.filter(parent_type='task', parent_id=self.id).delete()
        Attachment.objects.filter(parent_type='task', parent_id=self.id).delete()

        super(Task, self).delete(*args, **kwargs)

    class Meta:
        default_permissions = []


class SubtaskStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            SubtaskStatus.objects.all().update(default=False)

        super(SubtaskStatus, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []
        verbose_name_plural = "Subtask Statuses"


class Subtask(models.Model):
    project = models.ForeignKey(Project, related_name='subtask_project', on_delete=models.PROTECT)
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()

    name = models.CharField(max_length=40)
    description = models.TextField(null=True, blank=True)
    status = models.ForeignKey(SubtaskStatus, related_name='subtask_status', on_delete=models.PROTECT)
    assignee = models.ForeignKey(User, related_name='subtask_assignee', null=True, blank=True,
                                 on_delete=models.SET_NULL)

    bids = models.FloatField(default=0)
    actuals = models.IntegerField(default=0)
    work_perc = models.SmallIntegerField(default=0)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        Note.objects.filter(parent_type='task', parent_id=self.id).delete()
        ChangeLog.objects.filter(parent_type='task', parent_id=self.id).delete()
        Attachment.objects.filter(parent_type='task', parent_id=self.id).delete()

        super(Subtask, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class NoteType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    order = models.IntegerField(default=1, help_text="Sort Order")

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            NoteType.objects.all().update(default=False)

        super(NoteType, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Note Types"


class Note(models.Model):
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()
    text = models.TextField()
    type = models.ForeignKey(NoteType, related_name='note_type', on_delete=models.PROTECT)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='note_created_by', on_delete=models.PROTECT)

    # temp field
    msi_record_code = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        default_permissions = []


class Attachment(models.Model):
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()

    name = models.CharField(max_length=40)
    size = models.IntegerField()
    type = models.CharField(max_length=40, null=True)
    file = models.FileField(upload_to=upload_attachment)
    restricted = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='attachment_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class ChangeLog(models.Model):
    project = models.ForeignKey(Project, related_name='changelog_project',
                                on_delete=models.SET_NULL, null=True, blank=True)
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()

    key = models.CharField(max_length=40)
    value = models.CharField(max_length=40)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='change_log_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notification_user', on_delete=models.PROTECT)
    text = models.TextField()
    read = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='notification_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class Dependency(models.Model):
    project = models.ForeignKey(Project, related_name='dependency_project', on_delete=models.PROTECT)
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()

    child_type = models.CharField(max_length=20)
    child_id = models.IntegerField()

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='dependency_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class FilerecordType(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class FilerecordStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            FilerecordStatus.objects.all().update(default=False)

        super(FilerecordStatus, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []


# todo: update in models.yaml
class Filerecord(models.Model):
    project = models.ForeignKey(Project, related_name='filerecord_project', on_delete=models.PROTECT)
    parent_type = models.CharField(max_length=20)
    parent_id = models.IntegerField()
    locations = models.ManyToManyField(Location, related_name='filerecord_locations')

    client_name = models.CharField(max_length=200)
    client_version = models.SmallIntegerField(default=0)
    name = models.CharField(max_length=200)
    version = models.SmallIntegerField(default=1)
    path = models.TextField()
    type = models.ForeignKey(FilerecordType, related_name='filerecord_type', on_delete=models.PROTECT)
    status = models.ForeignKey(FilerecordStatus, related_name='filerecord_status', on_delete=models.PROTECT)

    first_frame = models.IntegerField(default=0)
    last_frame = models.IntegerField(default=0)
    extension = models.CharField(null=True, blank=True, max_length=10)
    padding = models.SmallIntegerField(default=0)
    connector = models.CharField(max_length=1, default='.')  # this is required, don't remove
    is_sequence = models.BooleanField(default=False)

    resolution = models.CharField(max_length=100, null=True, blank=True)
    camera = models.CharField(max_length=100, null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='filerecord_created_by', on_delete=models.PROTECT)

    def all_locations(self):
        return ','.join(self.locations.values_list('name', flat=True))

    class Meta:
        default_permissions = []


# todo: update in models.yaml
class ProjectResource(models.Model):
    location = models.ForeignKey(Location, related_name='projectresource_location', on_delete=models.PROTECT)
    project = models.ForeignKey(Project, related_name='projectresource_project', on_delete=models.PROTECT)
    department = models.ForeignKey(Department, related_name='projectresource_department', on_delete=models.PROTECT)

    date = models.DateField()
    projected = models.FloatField(default=0)
    actual = models.FloatField(default=0)

    modified_by = models.ForeignKey(User, related_name='project_resource_modified_by', null=True, blank=True,
                                    on_delete=models.SET_NULL)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = []


class BidStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)

    bg_color = models.CharField(max_length=7, default='#ffffff')
    fg_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            BidStatus.objects.all().update(default=False)

        super(BidStatus, self).save(*args, **kwargs)

    def colored_name(self):
        return format_html('<span style="background: {}; color: {}; padding: 4px;">{}</span>',
                           self.bg_color, self.fg_color, self.name)

    colored_name.allow_tags = True

    class Meta:
        default_permissions = []


class Bid(models.Model):
    client = models.ForeignKey(Client, related_name='bid_client', on_delete=models.PROTECT)
    project = models.CharField(max_length=20)
    project_type = models.ForeignKey(ProjectType, related_name='bid_project_type', on_delete=models.PROTECT)
    name = models.CharField(max_length=40)

    stereo_budget = models.SmallIntegerField(default=80)
    stereo_minutes = models.FloatField(default=0)
    resolution = models.FloatField(default=1)
    fps = models.SmallIntegerField(default=24)

    start_date = models.DateField()
    end_date = models.DateField()
    status = models.ForeignKey(BidStatus, related_name='bid_status', on_delete=models.PROTECT)
    purchase_order = models.CharField(max_length=40, blank=True, null=True)
    invoice_number = models.CharField(max_length=40, blank=True, null=True)
    rejected_for = models.TextField(null=True, blank=True, help_text='Reason if bid is rejected')
    default_tasks = models.ManyToManyField(TaskType, related_name='bid_default_tasks')

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='bid_created_by', on_delete=models.PROTECT)

    modified_on = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name='bid_modified_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class BidShot(models.Model):
    bid = models.ForeignKey(Bid, related_name='bidshot_bid', on_delete=models.PROTECT)

    sequence = models.CharField(max_length=40, null=True, blank=True)
    shot = models.CharField(max_length=40, null=True, blank=True)
    task = models.CharField(max_length=40, null=True, blank=True)
    task_type = models.ForeignKey(TaskType, related_name='bidshot_task_type', on_delete=models.PROTECT)
    bids = models.FloatField(default=0)
    awarded = models.BooleanField(default=False)

    internal_eta = models.DateField(null=True)
    client_eta = models.DateField(null=True)
    first_frame = models.SmallIntegerField(null=True)
    last_frame = models.SmallIntegerField(null=True)

    plate_version = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    sup_note = models.TextField(null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='bidshot_created_by', on_delete=models.PROTECT)

    modified_on = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name='bidshot_modified_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


class BaseRate(models.Model):
    task_type = models.CharField(max_length=20, unique=True)
    rate = models.IntegerField()

    class Meta:
        default_permissions = []

    def __str__(self):
        return self.task_type


class BaseROP(models.Model):
    task_type = models.CharField(max_length=20, unique=True)
    rate = models.FloatField()

    class Meta:
        default_permissions = []

    def __str__(self):
        return self.task_type


class BidRate(models.Model):
    bid = models.ForeignKey(Bid, related_name='bidrate_bid', on_delete=models.PROTECT)
    task_type = models.ForeignKey(TaskType, related_name='bidrate_task_type', on_delete=models.PROTECT)

    base_rate = models.IntegerField(default=0)
    rate = models.IntegerField(default=0)

    modified_on = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name='bidrate_created_by', on_delete=models.PROTECT, null=True)

    class Meta:
        default_permissions = []


class BidActual(models.Model):
    project = models.ForeignKey(Project, related_name='bidactual_project', on_delete=models.PROTECT)
    shot = models.ForeignKey(Shot, related_name='bidactual_shot', on_delete=models.PROTECT)
    task = models.ForeignKey(Task, related_name='bidactual_task', on_delete=models.PROTECT)
    subtask = models.ForeignKey(Subtask, related_name='bidactual_subtask', on_delete=models.PROTECT)

    user = models.ForeignKey(User, related_name='bidactual_artist', on_delete=models.PROTECT)
    date = models.DateField()
    actuals = models.IntegerField(default=0)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = []


class EmailGroup(models.Model):
    name = models.CharField(max_length=40, unique=True)
    mail_to = models.TextField(help_text='separate by ;')
    cc_to = models.TextField(help_text='separate_by ;', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = []


class Announcement(models.Model):
    text = models.TextField()
    valid_till = models.DateField()

    created_by = models.ForeignKey(User, related_name='announcement_created_by', on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = []


class ResourceCache(models.Model):
    department = models.ForeignKey(Department, related_name='resource_cache_department', on_delete=models.PROTECT)
    date = models.DateField()
    headcount = models.SmallIntegerField(default=0)
    absent = models.SmallIntegerField(default=0)
    leave = models.SmallIntegerField(default=0)
    working_hours = models.SmallIntegerField(default=8)

    # below fields are used for weekly cache
    mandays = models.SmallIntegerField(default=0)
    allocated = models.SmallIntegerField(default=0)
    borrowed_resources = models.SmallIntegerField(default=0)
    lend_resources = models.SmallIntegerField(default=0)
    weekdays = models.SmallIntegerField(default=0)
    weekly = models.BooleanField(default=False)

    class Meta:
        default_permissions = []


class ResourceShare(models.Model):
    from_department = models.ForeignKey(Department, related_name='resource_share_from_department',
                                        on_delete=models.PROTECT)
    to_department = models.ForeignKey(Department, related_name='resource_share_to_department',
                                      on_delete=models.PROTECT)
    date = models.DateField()
    count = models.FloatField(default=0)

    class Meta:
        default_permissions = []


class Workstation(models.Model):
    cpu = models.CharField(max_length=100, null=True, blank=True)
    ram = models.CharField(max_length=100, null=True, blank=True)
    ip = models.CharField(max_length=20, null=True, blank=True)
    mac = models.CharField(max_length=20, null=True, blank=True)
    hdd = models.TextField(null=True, blank=True)
    hostname = models.CharField(max_length=100, null=True, blank=True)
    gpu = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=200, null=True, blank=True)
    user = models.CharField(max_length=200, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True)

    # store system manufacturer
    sys_vendor = models.CharField(max_length=200, null=True, blank=True)
    product_name = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        default_permissions = []


class FileTransfer(models.Model):
    from_path = models.TextField(null=True, blank=True)
    to_path = models.TextField(null=True, blank=True)
    size = models.CharField(max_length=20, default=0)
    files = models.SmallIntegerField(default=0)
    status = models.CharField(max_length=20, null=True, blank=True)
    percent = models.SmallIntegerField(default=0)

    cancel = models.BooleanField(default=False)
    canceled_by = models.ForeignKey(User, related_name='filetransfer_canceled_by', null=True, on_delete=models.SET_NULL)

    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='filetransfer_created_by', on_delete=models.PROTECT)

    class Meta:
        default_permissions = []


# Todo: update on models.yaml
class PostOption(models.Model):
    title = models.TextField()
    link = models.URLField(null=True, blank=True)

    class Meta:
        default_permissions = []


# Todo: update on models.yaml
class Post(models.Model):
    title = models.TextField()
    options = models.ManyToManyField(PostOption)
    created_on = models.DateTimeField(auto_now_add=True)
    valid_till = models.DateTimeField()

    class Meta:
        default_permissions = []


# Todo: update on models.yaml
class Vote(models.Model):
    user = models.ForeignKey(User, related_name='vote_users', on_delete=models.PROTECT)
    post = models.ForeignKey(Post, related_name='vote_post', on_delete=models.PROTECT)
    option = models.ForeignKey(PostOption, related_name='vote_post_option', on_delete=models.PROTECT)

    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = []


class GmailGroup(models.Model):
    api_id = models.CharField(max_length=20, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    members = models.ManyToManyField(User)

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = []


class TicketPriority(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ProjectStatus.objects.all().update(default=False)

        super(TicketPriority, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Ticket Priorities"


class TicketStatus(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=1)
    locked = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ProjectStatus.objects.all().update(default=False)

        super(TicketStatus, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Ticket Statuses"


class TicketType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.default:
            ProjectStatus.objects.all().update(default=False)

        super(TicketType, self).save(*args, **kwargs)

    class Meta:
        default_permissions = []
        verbose_name_plural = "Ticket Types"


class Ticket(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

    priority = models.ForeignKey(TicketPriority, related_name='ticket_priority', on_delete=models.PROTECT)
    type = models.ForeignKey(TicketType, related_name='ticket_type', on_delete=models.PROTECT)
    status = models.ForeignKey(TicketStatus, related_name='ticket_status', on_delete=models.PROTECT)
    project = models.ForeignKey(Project, related_name='ticket_project', on_delete=models.SET_NULL, null=True,
                                blank=True)

    assigned_to = models.ForeignKey(User, related_name='ticket_assignee', on_delete=models.PROTECT,
                                    null=True, blank=True)
    assigned_on = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, related_name='ticket_created_by', on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True)

    resolved_by = models.ForeignKey(User, related_name='ticket_resolved_by', on_delete=models.SET_NULL,
                                    null=True, blank=True)
    resolved_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        default_permissions = []
