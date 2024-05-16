# blog/models.py
from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.models import ContentType
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.content  # Or whatever you want to display as the string representation of a Post





class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.sender} -> {self.recipient}'


class Attachment(models.Model):
    
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    timestamp = models.DateTimeField(auto_now_add=True)



class GroupChat(models.Model):
    group_name = models.CharField(max_length=100)
    members = models.ManyToManyField(User)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_group_chats')
    administrators = models.ManyToManyField(User, related_name='administered_group_chats')
    picture = models.ImageField(upload_to='group_chat_pictures/', blank=True, null=True) 
    def __str__(self):
        return self.group_name

class GroupMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    group_chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content}'
    
class Attachmentg(models.Model):
    message = models.ForeignKey(GroupMessage, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    timestamp = models.DateTimeField(auto_now_add=True)