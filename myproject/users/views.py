from django.shortcuts import render, redirect
#from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from .forms import  SignUpForm
from django.contrib.auth import authenticate
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from users.forms import ProfileForm, form_validation_error
from users.models import Profile
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import CustomAuthenticationForm
from django.dispatch import receiver
key = settings.ENCRYTION_KEY

def encrypt_message(message):
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

def decrypt_message(encrypted_message):
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message)
    return decrypted_message.decode()



def register(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Check if the email is already in use
            email = form.cleaned_data.get("email")
            if User.objects.filter(email=email).exists():
                msg = 'This email address is already in use.'
            else:
                form.save()
                
                username = form.cleaned_data.get("username")
                raw_password = form.cleaned_data.get("password1")
                user = authenticate(username=username, password=raw_password)
                msg = 'User created - please <a href="/login">login</a>.'
                success = True
                return redirect("login")
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "users/register.html", {"form": form, "msg": msg, "success": success})


def signout(request):
    current_ip = request.META.get('REMOTE_ADDR')
    
    # Update the user's profile with the current IP address as oldip
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        profile.oldip = current_ip
        profile.save()
    logout(request)

    return redirect('login')

from django.contrib import messages
from users.forms import ProfileForm, form_validation_error
from users.models import Profile

@method_decorator(login_required(login_url='login'), name='dispatch')
class ProfileView(View):
    profile = None

    def dispatch(self, request, *args, **kwargs):
        self.profile, __ = Profile.objects.get_or_create(user=request.user)
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        context = {'profile': self.profile, 'segment': 'profile'}
        return render(request, 'users/profile.html', context)

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=self.profile)

        if form.is_valid():
            profile = form.save()
            profile.user.first_name = form.cleaned_data.get('first_name')
            profile.user.last_name = form.cleaned_data.get('last_name')
            profile.user.email = form.cleaned_data.get('email')
            profile.user.save()

            messages.success(request, 'Profile saved successfully')
        else:
            messages.error(request, form_validation_error(form))
        return redirect('profile')




def restricted_view(view_func):
    """
    Decorator to restrict access to authenticated users only.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def update_user_ip(sender, user, request, **kwargs):
    # Get the user's IP address from the request
    ip_address = request.META.get('REMOTE_ADDR')

    # Update the Profile model
    if hasattr(user, 'profile'):
        profile = user.profile
        # Update oldip with the current ip
        profile.oldip = profile.ip
        # Update ip with the new ip
        profile.ip = ip_address
        profile.save()

        # Create a notification message containing the old IP address
        
        old_ip_message = f"Your old IP address was: {profile.oldip}"
        messages.info(request, old_ip_message)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomAuthenticationForm

    def form_valid(self, form):
        # Perform the default action of logging the user in
        response = super().form_valid(form)
        # Redirect to the inbox page after successful login
        old_ip_message = f"Your old IP address was: {self.request.user.profile.oldip}"
        messages.success(self.request, old_ip_message)
        return HttpResponseRedirect(reverse_lazy('inbox'))

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try to authenticate using the username    
        user = authenticate(request, username=username, password=password, **kwargs)

        # If authentication succeeds, update the user's IP address
        if user is not None:
            update_user_ip(request, user)

        # If authentication fails with username, try with email
        if user is None:
            try:
                # Try to find the user by email
                user = User.objects.get(email=username)
                # Authenticate the user with the found email
                user = authenticate(request, username=user.username, password=password, **kwargs)
                # If authentication succeeds with email, update the user's IP address
                if user is not None:
                    update_user_ip(request, user)
            except User.DoesNotExist:
                pass

        return user
    


@login_required
def profile(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'users/profile.html', {'profile': profile})


