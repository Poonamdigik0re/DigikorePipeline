from django.forms import ModelForm
from django.forms.widgets import TextInput

from base.models import *


class ShotStatusForm(ModelForm):
    class Meta:
        model = ShotStatus
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class TaskStatusForm(ModelForm):
    class Meta:
        model = TaskStatus
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class TaskComplexityForm(ModelForm):
    class Meta:
        model = TaskComplexity
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class TaskPriorityForm(ModelForm):
    class Meta:
        model = TaskPriority
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class SubtaskStatusForm(ModelForm):
    class Meta:
        model = SubtaskStatus
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class FilerecordStatusForm(ModelForm):
    class Meta:
        model = FilerecordStatus
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class NoteTypeForm(ModelForm):
    class Meta:
        model = NoteType
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }


class BidStatusForm(ModelForm):
    class Meta:
        model = BidStatus
        fields = '__all__'
        widgets = {
            'bg_color': TextInput(attrs={'type': 'color'}),
            'fg_color': TextInput(attrs={'type': 'color'}),
        }
