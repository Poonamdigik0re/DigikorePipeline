from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'base'

    def ready(self):
        pass


#         post_save.connect(post_save_update_bid_rates, sender=BaseRate)

#         from base.models import Subtask, Task, Shot, Sequence, Asset, Assetgroup, LdapGroup
#         post_save.connect(post_save_create_folder, sender=Subtask)
#         post_save.connect(post_save_create_folder, sender=Task)
#         post_save.connect(post_save_create_folder, sender=Shot)
#         post_save.connect(post_save_create_folder, sender=Sequence)
#         post_save.connect(post_save_create_folder, sender=Asset)
#         post_save.connect(post_save_create_folder, sender=Assetgroup)
#         post_save.connect(post_save_ldapgroup, sender=LdapGroup)
#
#         # create default tasks
#         post_save.connect(post_save_create_shot, sender=Shot)
#         post_save.connect(post_save_create_task, sender=Task)


class DBRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'auth':
            return 'default'

        return 'slave'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, *args, **kwargs):
        return True


def post_save_create_folder(sender, instance, created, **kwargs):
    if created:
        from utils.celery import create_folder
        create_folder.delay(instance._meta.model_name, instance.id)


def post_save_ldapgroup(sender, instance, created, **kwargs):
    if created:
        from utils.celery import create_ldap_group
        create_ldap_group.delay(instance.name, instance.gid)


def post_save_create_shot(sender, instance, created, **kwargs):
    if created:
        from base.models import TaskStatus, TaskComplexity, TaskPriority, Task

        for task_type in instance.project.default_tasks.all():
            task = Task(project=instance.project, parent_type='shot', parent_id=instance.id,
                        name=task_type.name, type=task_type,
                        status=TaskStatus.objects.get(default=True),
                        complexity=TaskComplexity.objects.get(default=True),
                        priority=TaskPriority.objects.get(default=True))
            task.save()


def post_save_create_task(sender, instance, created, **kwargs):
    if created:
        from base.models import Task, Shot, Asset

        parent = None
        if instance.parent_type == 'shot':
            parent = Shot.objects.get(id=instance.parent_id)
        elif instance.parent_type == 'asset':
            parent = Asset.objects.get(id=instance.parent_id)

        if parent:
            if instance.working_first_frame == 0:
                instance.working_first_frame = parent.working_first_frame

            if not instance.working_last_frame == 0:
                instance.working_last_frame = parent.working_last_frame

            instance.save()

# def post_save_update_bid_rates(sender, instance, created, **kwargs):
#     from base.models import BidRate
#
#     BidRate.objects.filter(task_type=instance.task_type, bid__created_on__year=instance.date.year,
#                            bid__created_on__month=instance.date.month).update(base_rate=instance.rate)
