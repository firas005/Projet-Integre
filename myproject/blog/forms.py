
from django import forms
from .models import Message
from django.core.validators import EmailValidator
from django.contrib.auth.models import User
from .models import GroupChat


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

class GroupChatForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ['group_name', 'members']  # Include 'name' field in the form
        
    def __init__(self, *args, **kwargs):
        super(GroupChatForm, self).__init__(*args, **kwargs)
        self.fields['group_name'].required = True  # Make the 'name' field required


class GroupMessageForm(forms.Form):
    content = forms.CharField(label='Message', widget=forms.Textarea(attrs={'placeholder': 'Enter Your Message...', 'rows': 4}))

class SetGroupChatPictureForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ['picture']  # Assuming 'group_chat_id' is the field to identify the group chat

    def __init__(self, *args, **kwargs):
        super(SetGroupChatPictureForm, self).__init__(*args, **kwargs)
        