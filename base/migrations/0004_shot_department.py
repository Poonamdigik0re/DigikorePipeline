# Generated by Django 3.2.18 on 2023-06-17 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_project_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='shot',
            name='department',
            field=models.ManyToManyField(related_name='shot_department', to='base.Department'),
        ),
    ]
