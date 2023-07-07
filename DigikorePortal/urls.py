from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
import base.views
from base import api

from base import artist_utilization
# from base import asset_library
from base import uploadFile
from base import attendance
from base import bidding_shots
from base import bidding_system
from base import clients_list
from base import employee_manager
from base import file_transfer
from base import gmail_group
from base import home
from base import ingest_system
from base import leave_manager
from base import digikore_team
from base import my_calendar
from base import my_profile
from base import posts
from base import project_archival
from base import projects
from base import projects_list
from base import projects_overview
from base import projects_permission
from base import resource_planner
from base import rv
from base import site_sync
from base import task_overview
from base import tasks_list
from base import team_manager
from base import tickets
from base import transportation
from base import vehicle_directory
from base import vendors_list
from base import workstations
from base import shots_list
from base import upload_shot
from base import upload_task

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(template_name='index.html', redirect_authenticated_user='/')),
    path('logout/', auth_views.LogoutView.as_view(next_page='/')),
    path('login_as/', base.views.login_as),
]

urlpatterns.extend([
    path('api/user_is_artist/<str:username>/', api.user_is_artist),
    path(
        'api/update_actuals/<str:project_name>/<str:sequence_name>/<str:shot_name>/<str:task_name>/<str:subtask_name>/<str:username>/<str:task_type>/',
        api.update_actuals),
    path('api/update_actuals_v2/', api.update_actuals_v2),
    path('api/save_system_info/', api.save_system_info),
    path('api/signiant/job_submit/', api.signiant_job_submit),
])

# Global Calls
urlpatterns.extend([
    path('base/get_user_details/', base.views.get_user_details),
    # path('base/get_username/', base.views.get_username),

    path('base/get_all_locations/', base.views.get_all_locations),
    path('base/get_all_designations/', base.views.get_all_designations),
    path('base/get_all_departments/', base.views.get_all_departments),
    path('base/get_all_shifts/', base.views.get_all_shifts),
    path('base/get_all_task_type/', base.views.get_all_task_type),
    path('base/get_all_holidays/', base.views.get_all_holidays),

    path('base/change_password/', base.views.change_password),

    path('base/add_note/', base.views.add_note),
    path('base/get_notes/', base.views.get_notes),
    path('base/get_note_types/', base.views.get_note_types),
    path('base/get_model_info/', base.views.get_model_info),

    path('base/add_attachments/', base.views.add_attachments),
    path('base/get_attachments/', base.views.get_attachments),
    path('base/get_change_logs/', base.views.get_change_logs),

    path('browse/', base.views.browse),

    # todo: move them out of base to employee manager
    path('base/get_all_skills/', base.views.get_all_skills),
    path('base/get_all_confirmation_status/', base.views.get_all_confirmation_status),
])

# Home
urlpatterns.extend([
    path('', home.home),
    path('home/get_upcoming_birthdays/', home.get_upcoming_birthdays),
    path('home/get_announcements/', home.get_announcements),
    path('home/add_announcement/', home.add_announcement),
])

# Employee Manager
urlpatterns.extend([
    path('employee_manager/', employee_manager.home),
    path('employee_manager/get_all_employees/', employee_manager.get_all_employees),
    path('employee_manager/get_employee_profile/', employee_manager.get_employee_profile),
    path('employee_manager/add_new_employee/', employee_manager.add_new_employee),
    path('employee_manager/download_as_csv/', employee_manager.download_as_csv),
])

# Leave Manager
urlpatterns.extend([
    path('leave_manager/', leave_manager.home),

    path('leave_manager/get_leave_count/', leave_manager.get_leave_count),
    path('leave_manager/get_leave_log/', leave_manager.get_leave_log),

    path('leave_manager/get_all_leaves/', leave_manager.get_all_leaves),
    path('leave_manager/apply_leave/', leave_manager.apply_leave),
    path('leave_manager/cancel_leave/', leave_manager.cancel_leave),
    path('leave_manager/reject_leave/', leave_manager.reject_leave),
    path('leave_manager/approve_leave/', leave_manager.approve_leave),

    path('leave_manager/get_all_comp_offs/', leave_manager.get_all_comp_offs),
    path('leave_manager/get_all_late_marks/', leave_manager.get_all_late_marks),

])

# Attendnace
urlpatterns.extend([
    path('attendance/', attendance.home),
])

# Team Manager
urlpatterns.extend([
    path('team_manager/', team_manager.home),
    path('team_manager/get_all_teams/', team_manager.get_all_teams),
    path('team_manager/get_all_employees/', team_manager.get_all_employees),
    path('team_manager/add_new_team/', team_manager.add_new_team),
    path('team_manager/add_team_member/', team_manager.add_team_member),
    path('team_manager/download_as_csv/', team_manager.download_as_csv),
])

# Clients List
urlpatterns.extend([
    path('clients_list/', clients_list.home),
    path('clients_list/get_all_clients/', clients_list.get_all_clients),
    path('clients_list/get_all_projects/', clients_list.get_all_projects),
    path('clients_list/get_all_contacts/', clients_list.get_all_contacts),

    path('clients_list/add_new_client/', clients_list.add_new_client),
    path('clients_list/add_new_contact/', clients_list.add_new_contact),
])

# Vendors List
urlpatterns.extend([
    path('vendors_list/', vendors_list.home),

    path('vendors_list/get_all_vendors/', vendors_list.get_all_vendors),
    path('vendors_list/get_all_projects/', vendors_list.get_all_projects),
    path('vendors_list/get_all_contacts/', vendors_list.get_all_contacts),

    path('vendors_list/add_new_vendor/', vendors_list.add_new_vendor),
    path('vendors_list/add_new_contact/', vendors_list.add_new_contact),
])

# Projects List
urlpatterns.extend([
    path('projects_list/', projects_list.home),
    path('projects_list/get_project_defaults/', projects_list.get_project_defaults),
    path('projects_list/get_client_contacts/', projects_list.get_client_contacts),
    path('projects_list/get_all_projects/', projects_list.get_all_projects),
    path('projects_list/add_new_project/', projects_list.add_new_project),
])

# Projects Overview
urlpatterns.extend([
    path('projects_overview/<int:project_id>/', projects_overview.home),
    path('projects_overview/<int:project_id>/get_project_data/', projects_overview.get_project_data),
])

# Projects Permission
urlpatterns.extend([
    path('projects_permission/<int:project_id>/', projects_permission.home),
    path('projects_permission/<int:project_id>/get_users/', projects_permission.get_users),
    path('projects_permission/<int:project_id>/save_permissions/', projects_permission.save_permissions),
])

# Project
urlpatterns.extend([
    path('projects/<int:project_id>/', projects.home),
    path('projects/<int:project_id>/get_defaults/', projects.get_defaults),
    path('projects/<int:project_id>/get_data/', projects.get_data),
    path('projects/<int:project_id>/update_model/', projects.update_model),
    path('projects/<int:project_id>/update_selected_tasks/', projects.update_selected_tasks),

    path('projects/<int:project_id>/download_as_csv/', projects.download_as_csv),
    path('projects/<int:project_id>/get_filter_data/', projects.get_filter_data),
    path('projects/<int:project_id>/get_filter_values/', projects.get_filter_values),
    path('projects/<int:project_id>/download_actuals_breakdown/', projects.download_actuals_breakdown),
    path('projects/<int:project_id>/download_artist_actuals_breakdown/', projects.download_artist_actuals_breakdown),
    path('projects/<int:project_id>/download_aggregated_actuals_report/', projects.download_aggregated_actuals_report),
])

# Asset Library
urlpatterns.extend([
    path('tasks_list/', tasks_list.home),
    path('tasks_list/get_all_users/', tasks_list.get_all_users),
    path('tasks_list/get_user_tasks/', tasks_list.get_user_tasks),
    path('tasks_list/get_projects/', tasks_list.get_projects),
    path('tasks_list/get_task_status/', tasks_list.get_task_status),
    path('tasks_list/get_task_priority/', tasks_list.get_task_priority),
    path('tasks_list/get_assignee/', tasks_list.get_assignee),
    path('tasks_list/add_new_task/', tasks_list.add_new_task),
])

# # Asset Library
# urlpatterns.extend([
#     path('asset_library/', asset_library.home),
#     path('asset_library/get_all_assets/', asset_library.get_all_assets),
# ])

urlpatterns.extend([
    path('resource_planner/', resource_planner.home),
    path('resource_planner/get_departments/', resource_planner.get_departments),

    path('resource_planner/get_headcount/', resource_planner.get_headcount),
    path('resource_planner/get_working_hours/', resource_planner.get_working_hours),
    path('resource_planner/get_resource_share/', resource_planner.get_resource_share),
    path('resource_planner/get_leaves/', resource_planner.get_leaves),
    path('resource_planner/get_absents/', resource_planner.get_absents),
    path('resource_planner/get_holidays/', resource_planner.get_holidays),
    path('resource_planner/get_projects/', resource_planner.get_projects),
    path('resource_planner/get_resources/', resource_planner.get_resources),
    path('resource_planner/update_working_hours/', resource_planner.update_working_hours),
    path('resource_planner/add_resources/', resource_planner.add_resources),
    path('resource_planner/add_resource_share/', resource_planner.add_resource_share),
    path('resource_planner/get_annual_projection/', resource_planner.get_annual_projection),
    path('resource_planner/get_annual_charts/', resource_planner.get_annual_charts),

    path('resource_planner/download_as_csv/', resource_planner.download_as_csv),
])

# Overview
urlpatterns.extend([
    path('task_overview/<int:task_id>/', task_overview.home),
    path('task_overview/<int:task_id>/get_defaults/', task_overview.get_defaults),
    path('task_overview/<int:task_id>/get_data/', task_overview.get_data),
    path('task_overview/<int:task_id>/add_subtask/', task_overview.add_subtask),
    path('task_overview/<int:task_id>/get_bidactuals/', task_overview.get_bidactuals),
])

# Ingest System
urlpatterns.extend([
    path('ingest_system/', ingest_system.home),
    path('ingest_system/get_defaults/', ingest_system.get_defaults),
    path('ingest_system/get_projects/', ingest_system.get_projects),
    path('ingest_system/get_parents/', ingest_system.get_parents),
    path('ingest_system/get_data/', ingest_system.get_data),
    path('ingest_system/get_version/', ingest_system.get_version),
    path('ingest_system/start_ingest/', ingest_system.start_ingest),
])

# Ingest System
urlpatterns.extend([
    path('bidding_system/', bidding_system.home),
    path('bidding_system/get_defaults/', bidding_system.get_defaults),
    path('bidding_system/get_client_projects/', bidding_system.get_client_projects),
    path('bidding_system/get_all_bids/', bidding_system.get_all_bids),
    path('bidding_system/add_bid/', bidding_system.add_bid),
    path('bidding_system/update_bid_status/', bidding_system.update_bid_status),

    path('bidding_system/get_base_rates/', bidding_system.get_base_rates),
    path('bidding_system/get_base_rop/', bidding_system.get_base_rop),
    path('bidding_system/get_bid_rates/', bidding_system.get_bid_rates),
    path('bidding_system/update_bid_rates/', bidding_system.update_bid_rates),

    path('bidding_system/download_summary/', bidding_system.download_summary),
])

# Artist Utilization
urlpatterns.extend([
    path('artist_utilization/', artist_utilization.home),
    path('artist_utilization/get_departments/', artist_utilization.get_departments),
    path('artist_utilization/get_data/', artist_utilization.get_data),
    path('artist_utilization/download_as_csv/<str:date>/', artist_utilization.download_as_csv),
])

# Bidding System
urlpatterns.extend([
    path('bidding_shots/<int:bid_id>/', bidding_shots.home),
    path('bidding_shots/<int:bid_id>/get_defaults/', bidding_shots.get_defaults),
    path('bidding_shots/<int:bid_id>/get_bidshots/', bidding_shots.get_bidshots),
    path('bidding_shots/<int:bid_id>/save_bidshots/', bidding_shots.save_bidshots),
    path('bidding_shots/<int:bid_id>/download_bidshots/', bidding_shots.download_bidshots),

    path('bidding_shots/<int:bid_id>/get_bid_status/', bidding_shots.get_bid_status),
    path('bidding_shots/<int:bid_id>/update_bid_status/', bidding_shots.update_bid_status),
])

# Site Sync
urlpatterns.extend([
    path('site_sync/', site_sync.home),
    path('site_sync/get_status_breakdown/<str:location>/', site_sync.get_status_breakdown),
    path('site_sync/get_project_breakdown/<str:location>/', site_sync.get_project_breakdown),
    path('site_sync/fix_sig_submitted/', site_sync.fix_sig_submitted),
])

# My Profile
urlpatterns.extend([
    path('my_profile/', my_profile.home)
])

# Digikore Team
urlpatterns.extend([
    path('digikore_team/', digikore_team.home),
    path('digikore_team/get_all_employees/', digikore_team.get_all_employees),
])

# Workstations
urlpatterns.extend([
    path('workstations/', workstations.home),
    path('workstations/get_all_workstations/', workstations.get_all_workstations),
])

urlpatterns.extend([
    path('my_calendar/', my_calendar.home),
    path('my_calendar/get_my_attendance/', my_calendar.get_my_attendance),
])

# copy data
urlpatterns.extend([
    path('file_transfer/', file_transfer.home),
    path('file_transfer/get_active_transfers/', file_transfer.get_active_transfers),
    path('file_transfer/browse/', file_transfer.browse),
    path('file_transfer/add_folder/', file_transfer.add_folder),
    path('file_transfer/start_transfer/', file_transfer.start_transfer),
    path('file_transfer/cancel_transfer/', file_transfer.cancel_transfer),
    path('file_transfer/restart_transfer/', file_transfer.restart_transfer),
])

# Project Archival
urlpatterns.extend([
    path('project_archival/', project_archival.home),
    path('project_archival/get_projects/', project_archival.get_projects),
    path('project_archival/start_archival/', project_archival.start_archival),
])

# RV Webview
urlpatterns.extend([
    path('rv/', rv.home),
    path('rv/get_projects/', rv.get_projects),
])

# Transportation Page
urlpatterns.extend([
    path('transportation/', transportation.home),
    path('transportation/get_employees/', transportation.get_employees),
    path('transportation/download_as_csv/', transportation.download_as_csv),
])

# Vehicle Directory
urlpatterns.extend([
    path('vehicle_directory/', vehicle_directory.home),
    path('vehicle_directory/get_employees/', vehicle_directory.get_employees),
    path('vehicle_directory/download_as_csv/', vehicle_directory.download_as_csv),
])

# Posts
urlpatterns.extend([
    path('posts/', posts.home),
    path('posts/get_all_posts/', posts.get_all_posts),
    path('posts/<int:post_id>/', posts.post_home),
    path('posts/<int:post_id>/get_post_options/', posts.get_post_options),
    path('posts/<int:post_id>/vote/', posts.vote),

])

# Gmail Group
urlpatterns.extend([
    path('gmail_group/', gmail_group.home),
    path('gmail_group/get_all_groups/', gmail_group.get_all_groups),
    path('gmail_group/get_all_users/', gmail_group.get_all_users),
    path('gmail_group/create_group/', gmail_group.create_group),
])

urlpatterns.extend([
    path('tickets/', tickets.home),
    path('tickets/get_defaults/', tickets.get_defaults),
    path('tickets/get_all_tickets/', tickets.get_all_tickets),
    path('tickets/add_ticket/', tickets.add_ticket),
    path('uploadfile/',uploadFile.home),

    path('tickets/<int:ticket_id>/', tickets.ticket_home),
    path('tickets/<int:ticket_id>/get_ticket_details/', tickets.get_ticket_details),
    path('tickets/<int:ticket_id>/add_note/', tickets.add_note),
    path('tickets/<int:ticket_id>/get_notes/', tickets.get_notes),
    path('tickets/<int:ticket_id>/update_ticket/', tickets.update_ticket)

])

#upload_task CSV
urlpatterns.extend([
    path('task_list/upload_task/', upload_task.home),
    path('task_list/upload_task/upload_csv/', upload_task.upload_csv),
    path('task_list/upload_task/update_csv/', upload_task.update_csv),
    path('task_list/upload_task/submit_csv/', upload_task.submit_csv),

])

# shot
urlpatterns.extend([
    path('shot_list/', shots_list.home),
    path('shot_list/get_all_shots/', shots_list.get_shots),
    path('shot_list/get_all_users/', shots_list.get_all_users),
    path('shot_list/upload_shot/', upload_shot.home),
    path('shot_list/upload_shot/submit_csv/', upload_shot.submit_csv),
    path('shot_list/upload_shot/upload_csv/', upload_shot.upload_csv),
    path('shot_list/upload_shot/update_csv/', upload_shot.update_csv),
])

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
