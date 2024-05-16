from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path,include
from users import views as user_views
from blog import views as blog_views
from django.conf import settings
from django.conf.urls.static import static
from blog.views import contactus, success
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/',user_views.register,name='register'),
    path('',include("blog.urls")),#include to send people to that route w '' is home page(ne)
    path('login/',user_views.CustomLoginView.as_view(template_name='users/login.html'),name='login'),
    path('logout/',user_views.signout,name='logout'),
    path('profile/',user_views.Profile,name='profile'),
    path('contact-us/', blog_views.contactus, name='contactus'),
    #path('logout/',auth_views.LogoutView.as_view(template_name='users/logout.html'),name='logout'),
    path('users/', include("users.urls")),  # Django users route
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEVEL:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)