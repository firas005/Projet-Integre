from django.urls import path
from users import views  # Change from 'customers' to 'users'
from django.urls import path, include

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('',include("blog.urls")),
    
]
