#to create profile without amdin page
from django.db.models.signals import  post_save
from django.contrib.auth.models import User #the sender
from django.dispatch import receiver 
from.models  import Profile
#importing the models for referencing them in signals

@receiver(post_save , sender =User) #the receiver is create profile
def create_profile(sender,instance,created,**kwargs):
    if created:
        Profile.objects.create(user=instance)
@receiver(post_save , sender =User) #the receiver is save profile
def save_profile(sender, instance , **kwargs):
    instance.profile.save()
