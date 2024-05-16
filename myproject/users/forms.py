from django import forms 
from django.contrib.auth.models import User 
from django.contrib.auth.forms import UserCreationForm
from users.models import Profile  # Changed from 'customers.models' to 'users.models'
from django.core.exceptions import ValidationError

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Username",                
                "class": "form-control"
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder" : "Email",                
                "class": "form-control"
            }
        ))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Password",                
                "class": "form-control"
            }
        ))
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Password check",                
                "class": "form-control"
            }
        ))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


from django import forms
from users.models import Profile  # Changed from 'customers.models' to 'users.models'
from django.contrib.auth.forms import AuthenticationForm

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = '__all__'
        exclude = ['user']





def form_validation_error(form):
    msg = ""
    for field in form:
        for error in field.errors:
            msg += "%s: %s \\n" % (field.label if hasattr(field, 'label') else 'Error', error)
    return msg


class CustomAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        # Check if the input is a valid email address
        username = self.cleaned_data.get('username')

        if '@' in username:
            # If it's an email address, try to find the corresponding user
            try:
                print("email")
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                # If no user is found with the given email, raise a validation error

                raise ValidationError('No user found with this email address.')
        else:
            # Otherwise, return the provided username
            return username