
from django import forms
from .models import Message
from django.core.validators import EmailValidator
from django.contrib.auth.models import User
class MessageForm(forms.ModelForm):
    recipient_username = forms.CharField(max_length=150, label='Recipient Username')

    class Meta:
        model = Message
        fields = ['recipient_username', 'content']

    def clean_recipient_username(self):
        username = self.cleaned_data['recipient_username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"User '{username}' does not exist.")
        return user

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100,required=True)
    last_name = forms.CharField(max_length=100,required=True)
    email = forms.CharField(validators=[EmailValidator()])
    message= forms.CharField(widget=forms.Textarea,required=True)
