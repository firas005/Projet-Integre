from.import views
from django.urls import path
from . import views
from .views import blocked_users
urlpatterns = [
    path("", views.chat  # the function home in views.py
         , name="chat"),
    path("about/", views.about # the function home in views.py
         , name="blogabout"),  
     path("contactus/", views.contactus , name="contactus") ,
     path('post_message/', views.post_message, name='post_message'),
     path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
     path('send-message/', views.send_message, name='send_message'),
     path('inbox/', views.inbox, name='inbox'),
     path('inbox/<str:contact>/', views.inbox, name='inbox_with_contact'),
     path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
     path('success/', views.success, name="success"),
     path('block-user/', views.block_user, name='block_user'),
     path('unblock_user/', views.unblock_user, name='unblock_user'),
     
     path('blocked-users/', blocked_users, name='blocked_users'),
     path('blocked-by-users/', views.blocked_by_users, name='blocked_by_users'),
]
