from django import forms
from .models import Prompt, BotFile

class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ['prompt_text']
        widgets = {
            'prompt_text': forms.Textarea(attrs={'rows': 15, 'class': 'form-control'}),
        }

class BotFileForm(forms.ModelForm):
    class Meta:
        model = BotFile
        fields = ['name', 'file', 'file_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
