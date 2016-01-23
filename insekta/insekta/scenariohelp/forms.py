from django import forms

class NewQuestionForm(forms.Form):
    title = forms.CharField(max_length=120)
    text = forms.CharField(widget=forms.Textarea())