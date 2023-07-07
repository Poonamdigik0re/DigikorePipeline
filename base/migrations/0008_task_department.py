# Generated by Django 3.2.18 on 2023-06-17 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_remove_task_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='department',
            field=models.ManyToManyField(related_name='task_department', to='base.Department'),
        ),
    ]
