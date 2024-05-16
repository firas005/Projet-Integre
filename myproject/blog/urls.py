from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from . import views

from .views import blocked_users

urlpatterns = [
    # Chat-related paths
    path("", login_required(views.chat), name="chat"),
    path("about/", views.about, name="blogabout"),  
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
    path('clear_scroll_to_bottom/', views.clear_scroll_to_bottom, name='clear_scroll_to_bottom'),
    path('blocked-users/', blocked_users, name='blocked_users'),
    path('blocked-by-users/', views.blocked_by_users, name='blocked_by_users'),
    path('create_group_chat/', views.create_group_chat, name='create_group_chat'),
    path('group_chat_inbox/', views.group_chat_inbox, name='group_chat_inbox'),
    path('group_chat_inbox/<int:group_chat_id>/', views.group_chat_inbox, name='group_chat_inbox'),
    path('post_group_message/<int:group_chat_id>/', views.post_group_message, name='post_group_message'),
    path('handle_message/', views.handle_message, name="handle_message"),
    path('group_chat/<int:group_chat_id>/admin/', views.group_chat_admin, name='group_chat_admin'),
    path('add_user_to_group_chat/', views.add_user_to_group_chat, name='add_user_to_group_chat'),
    path('remove_user_from_group_chat/', views.remove_user_from_group_chat, name='remove_user_from_group_chat'),
    path('set_group_chat_picture/', views.set_group_chat_picture, name='set_group_chat_picture'),
    path('add_administrator_to_group_chat/', views.add_administrator_to_group_chat, name='add_administrator_to_group_chat'),
    path('change_group_name/', views.change_group_name, name='change_group_name'),
    path('delete_messageg/<int:message_id>/', views.delete_messageG, name='delete_messageG'),
    path("index/", views.index, name="index"),
   
    # Authentication-related paths
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),

]

# Serve media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
