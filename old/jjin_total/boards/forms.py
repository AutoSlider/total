from django import forms
from .models import Board
# from markdownx.fields import MarkdownxFormField

class BoardCreateForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['input_type', 'input_text', 'input_youtube', 'input_video', ]
        widgets = {
            # base.html
            'input_type': forms.Select(choices=Board.input_type_choices, attrs={'class': 'input_type'}),
            'input_text': forms.Textarea(attrs={'id': 'input_text'}),
            'input_youtube': forms.TextInput(attrs={'id': 'input_youtube'}),
            'input_video': forms.ClearableFileInput(attrs={'id': 'input_video'}),
        }

# class BoardNoteForm(forms.ModelForm):
#     class Meta:
#         model = Board
#         # note = MarkdownxFormField()
#         fields = ['note']
#         # widgets = {
#         #     'note': forms.Textarea(attrs={'id': 'user_note'}),
#         # }
