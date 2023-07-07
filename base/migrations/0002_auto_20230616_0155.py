# Generated by Django 3.2.18 on 2023-06-16 01:55

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='msi_record_code',
        ),
        migrations.RemoveField(
            model_name='task',
            name='task_name',
        ),
        migrations.AddField(
            model_name='project',
            name='department',
            field=models.ManyToManyField(related_name='project_department', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='msi_sync',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='parent_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='parent_type',
            field=models.CharField(max_length=20, null=True),
        ),
    ]