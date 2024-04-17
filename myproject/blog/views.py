from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import MessageForm
from .models import Message
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from users.models import Profile
from cryptography.fernet import Fernet
from django.conf import settings
posts = [
    
]
key = settings.ENCRYTION_KEY

def encrypt_message(message):
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

def decrypt_message(encrypted_message):
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message)
    return decrypted_message.decode()

def chat(request):
    context = {
        'posts': posts
    }
    return render(request, 'blog/chat.html', context)


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def contactus(request):
    return render(request,'blog/contactus.html')

def chat(request):
    # Fetch all posts from the database
    posts = Post.objects.all().order_by('-date_posted')
    context = {
        'posts': posts
    }
    return render(request, 'blog/chat.html', context)

def delete_post(request, post_id):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient', '')
        # Fetch the post object by its ID
        
        post = Post.objects.get(pk=post_id)
        # Check if the current user is the author of the post (for security)
        if post.author == request.user:
            # Delete the post
            post.delete()
    return redirect('inbox_with_contact', contact=recipient_username)

def post_message(request):
    if request.method == 'POST':
        # Get the message content and recipient from the form
        message_content = request.POST.get('message', '')
        recipient_username = request.POST.get('recipient', '')
        
        # Get the recipient user object
        recipient = User.objects.get(username=recipient_username)
        
        # Encrypt the message content
        encrypted_content = encrypt_message(message_content)
        
        # Ensure the message content is not empty before saving
        if message_content.strip():
            # Check if the recipient has blocked the sender
            if recipient in request.user.profile.blocked_users.all():
                messages.error(request, f"You cannot send a message to {recipient_username}. You are blocked by this user.")
            # Check if the sender has blocked the recipient
            elif request.user in recipient.profile.blocked_users.all():
                messages.error(request, f"You cannot send a message to {recipient_username}. You have blocked this user.")
            else:
                # Create a new Message instance with user information and current date
                message = Message(sender=request.user, recipient=recipient, content=encrypted_content)
                message.save()
                messages.success(request, f"Message sent to {recipient_username} successfully.")
        else:
            messages.error(request, "Message content cannot be empty.")

    # Redirect to the inbox page after posting the message, with the selected contact as a parameter
    return redirect('inbox_with_contact', contact=recipient_username)

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['recipient_username']
            message_content = form.cleaned_data['content']

            try:
                recipient = User.objects.get(username=recipient_username)
            except User.DoesNotExist:
                error_message = f"The user '{recipient_username}' does not exist."
                form.add_error('recipient_username', error_message)  # Add the error to the form
                return render(request, 'messages/send_message.html', {'form': form})

            # Ensure that the recipient is not the same as the sender
            if recipient == request.user:
                error_message = "You cannot send a message to yourself."
                form.add_error('recipient_username', error_message)  # Add the error to the form
                return render(request, 'messages/send_message.html', {'form': form})

            # Check if the recipient is blocked by the sender
            if recipient in request.user.profile.blocked_users.all():
                error_message = f"You have blocked {recipient_username}. You cannot send messages to blocked users."
                form.add_error('recipient_username', error_message)  # Add the error to the form
                return render(request, 'messages/send_message.html', {'form': form})

            # Check if the sender is blocked by the recipient
            if request.user in recipient.profile.blocked_users.all():
                error_message = f"{recipient_username} has blocked you. You cannot send messages to users who have blocked you."
                form.add_error('recipient_username', error_message)  # Add the error to the form
                return render(request, 'messages/send_message.html', {'form': form})

            # Create a new Message instance with user information and current date
            encrypted_content = encrypt_message(message_content)
            message = Message(sender=request.user, recipient=recipient, content=encrypted_content)
            message.save()

            # Redirect to the inbox with the selected contact
            return redirect('inbox_with_contact', contact=recipient_username)
    else:
        form = MessageForm()
    return render(request, 'messages/send_message.html', {'form': form})




@login_required
def inbox(request, contact=None):
    try:
        # Fetch all messages where the current user is either the sender or the recipient
        messages = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('timestamp')

        # Group messages by conversation (combination of sender and recipient)
        conversations = {}
        for message in messages:
            if message.sender == request.user:
                other_user = message.recipient
            else:
                other_user = message.sender

            conversation_key = (request.user, other_user)

            if conversation_key not in conversations:
                conversations[conversation_key] = []

            # Attempt to decrypt the message content
            try:
                decrypted_message_content = decrypt_message(message.content[2:len(message.content)-1])
                message.content = decrypted_message_content 
            except Exception as e:
                # If decryption fails, log the error and set content to an error message
                
                message.content = "Decryption error: Unable to decrypt message content"
                
            conversations[conversation_key].append(message)

        # Get all users the current user had conversations with
        contacts = set()
        for key in conversations.keys():
            contacts.add(key[1])  # Add the other user in the conversation

        selected_contact = None
        selected_conversation = None  # Initialize selected_conversation as None initially
        if contact:
            selected_contact = User.objects.get(username=contact)
            selected_conversation_key = (request.user, selected_contact)
            selected_conversation = conversations.get(selected_conversation_key, [])

        return render(request, 'messages/inbox.html', {'contacts': contacts, 'selected_contact': selected_contact, 'selected_conversation': selected_conversation})
    except Exception as e:
        # If an unexpected error occurs, log the error and return a generic error message
        print(f"An unexpected error occurred: {e}")
        return render(request, 'messages/inbox.html', {'error': 'An unexpected error occurred. Please try again later.'})
    
@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    return render(request, 'messages/message_detail.html', {'message': message})

@login_required
def delete_message(request, message_id):
    # Fetch the message object by its ID
    message = get_object_or_404(Message, pk=message_id)
    
    # Get the recipient username from the message
    recipient_username = message.recipient.username
    
    # Check if the current user is the sender of the message
    if message.sender == request.user:
        # Delete the message
        message.delete()
        messages.success(request, 'Message deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this message.')
    
    # Redirect back to the inbox or conversation page
    return redirect('inbox_with_contact', contact=recipient_username)

@login_required
def block_user(request):
    if request.method == 'POST':
        user_to_block_username = request.POST.get('user_to_block', '')
        try:
            user_to_block = User.objects.get(username=user_to_block_username)
            request.user.profile.blocked_users.add(user_to_block)
            messages.success(request, f'You have blocked {user_to_block_username}.')
        except User.DoesNotExist:
            messages.error(request, f"The user '{user_to_block_username}' does not exist.")
    return redirect('inbox')

@login_required
def unblock_user(request):
    if request.method == 'POST':
        user_to_unblock_username = request.POST.get('user_to_unblock', '')
        try:
            user_to_unblock = User.objects.get(username=user_to_unblock_username)
            request.user.profile.blocked_users.remove(user_to_unblock)
            messages.success(request, f'You have unblocked {user_to_unblock_username}.')
        except User.DoesNotExist:
            messages.error(request, f"The user '{user_to_unblock_username}' does not exist.")
    return redirect('inbox')

@login_required
def blocked_users(request):
    blocked_users = request.user.profile.blocked_users.all()
    return render(request, 'messages/blocked_users.html', {'blocked_users': blocked_users})

def blocked_by_users(request):
    blocked_by_users = Profile.objects.filter(blocked_users=request.user)
    return render(request, 'messages/blocked_by_users.html', {'blocked_by_users': blocked_by_users})

from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ContactForm
from django.contrib import messages
from django.http import HttpResponse  # Add this import if not already present

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']  # Update variable name
            last_name = form.cleaned_data['last_name']  # Update variable name
            email = form.cleaned_data['email']  # Update variable name
            message = form.cleaned_data['message']  # Update variable name

            # Construct email message
            subject = f'New message from {name} {last_name}'  # Update variable name
            body = f'From: {email}\n\n{message}'
            sender_email = 'your_email@example.com'  # Replace with your email
            recipient_email = ['firasbenhmida23@gmail.com']  # Replace with recipient's email address

            # Send the mail
            send_mail(subject, body, sender_email, recipient_email)
            
            messages.success(request, 'Your message has been sent successfully! Thanks for your feedback')

            # Optionally, you can redirect to a success page
            return render(request, 'blog/chat.html', {'form': form})
        else:
            # Pass form errors to the template
            print(form.errors)
            return render(request, 'blog/contactus.html', {'form': form, 'error_message': 'Form is invalid'})
    else:
        form = ContactForm()
    
    # If it's a GET request or the form is invalid, render the contact form
    return render(request, 'blog/contactus.html', {'form': form})

def success(request):
    return HttpResponse('success')
