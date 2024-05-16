
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import OuterRef, Subquery
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
from .models import Attachment
from django.http import JsonResponse
from .models import GroupChat
from .forms import GroupChatForm, GroupMessageForm,SetGroupChatPictureForm
from .models import GroupChat,Attachmentg
from .models import GroupMessage
from django.http import HttpResponseForbidden, HttpResponseNotFound ,HttpResponseNotAllowed,HttpResponseBadRequest
from django.db.models import Q, Max

def clear_scroll_to_bottom(request):
    # Clear the session variable
    request.session.pop('scroll_to_bottom', None)
    return JsonResponse({'status': 'success'})  
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


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def chat(request): #affichage chat normal
    # Fetch all posts from the database
    posts = Post.objects.all().order_by('-date_posted')
    
    # Get all users except the current user
    conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    last_message_subquery = Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user),
                Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk')) #reference pk(primary key) :puts pk in recipient
            ).order_by('-timestamp').values('timestamp')[:1]

            # Fetch the contacts with whom the user has conversations and annotate the last message timestamp for each
    contacts = User.objects.annotate(   #fill the list with the objects 
    last_message_timestamp=Subquery(last_message_subquery)  #filter the user by the last one sent message or recieved one 
            ).exclude(username=request.user.username).filter(
                Q(sent_messages__in=conversations) | Q(received_messages__in=conversations)
            ).order_by('-last_message_timestamp').distinct()
    group_chats = GroupChat.objects.filter(members=request.user)
    context = {
        'posts': posts,
        'contacts': contacts,
        'group_chats':group_chats
    }
    return render(request, 'blog/chat2.html', context)

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
    print("In post message")
    if request.method == 'POST':
        print("Inside post")
        print("post", request.POST)
        message_content = request.POST.get('message', '')
        print("f",message_content)
        recipient_username = request.POST.get('recipient', '')
        print("f",recipient_username)
        attachments = request.FILES.getlist('attachment', [])
        print("f",attachments)
        try:
            if not recipient_username:
                raise ValueError("Recipient username is empty")

            recipient = User.objects.get(username=recipient_username)

            encrypted_content = encrypt_message(message_content)

            if message_content.strip():
                if recipient.profile.blocked_users.filter(username=request.user.username).exists():
                    messages.error(request, f"You cannot send a message to {recipient_username}. You are blocked by this user.")
                elif request.user.profile.blocked_users.filter(username=recipient_username).exists():
                    messages.error(request, f"You cannot send a message to {recipient_username}. You have blocked this user.")
                else:
                    message = Message(sender=request.user, recipient=recipient, content=encrypted_content)
                    message.save()

                    for attachment in attachments:
                        Attachment.objects.create(message=message, file=attachment)
                    
                    # Return success response as JSON
                    return JsonResponse({'success': True, 'message': f"Message sent to {recipient_username} successfully."})
            else:
                messages.error(request, "Message content cannot be empty.")
        except User.DoesNotExist:
            messages.error(request, f"Recipient with username {recipient_username} does not exist.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        # Return error response as JSON
        return JsonResponse({'success': False, 'error': 'Failed to send message.'})

    else:
        # Handle other HTTP methods (e.g., GET) gracefully
        return JsonResponse({'success': False, 'error': 'Method not allowed.'})
@login_required

def send_message(request): #sends messages in a conversation and handles attachements
    error_message = None
    group_chats = GroupChat.objects.filter(members=request.user)
    conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    last_message_subquery = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk'))
        ).order_by('-timestamp').values('timestamp')[:1]

        # Fetch the contacts and annotate the last message timestamp for each
    contacts = User.objects.annotate(
            last_message_timestamp=Subquery(last_message_subquery)
        ).exclude(username=request.user.username).order_by('-last_message_timestamp')
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['recipient_username']
            message_content = form.cleaned_data['content']

            try:
                recipient = User.objects.get(username=recipient_username)
            except User.DoesNotExist:
                error_message = f"The user '{recipient_username}' does not exist."
            else:
                if recipient == request.user:
                    error_message = "You cannot send a message to yourself."
                elif recipient in request.user.profile.blocked_users.all():
                    error_message = f"You have blocked {recipient_username}. You cannot send messages to blocked users."
                elif request.user in recipient.profile.blocked_users.all():
                    error_message = f"{recipient_username} has blocked you. You cannot send messages to users who have blocked you."
                else:
                    encrypted_content = encrypt_message(message_content)
                    message = Message(sender=request.user, recipient=recipient, content=encrypted_content)
                    message.save()

                    messages.success(request, f"Message sent to {recipient_username} successfully.")
                    return redirect('inbox_with_contact', contact=recipient_username)
        else:
            # Form is invalid, set error_message
            error_message = ""
            # Add error messages from the form to the error_message
            for field_errors in form.errors.values():
                for error in field_errors:
                    error_message += f" {error}"

    else:
        form = MessageForm()

    return render(request, 'blog/chat2.html', {'form': form, 'error_message': error_message, 'contacts': contacts, 'group_chats':group_chats})



@login_required
def inbox(request, contact=None): #show messages in a conversations along attachements if there a selected contact
    message_type = "contact"
    group_chats = GroupChat.objects.filter(members=request.user)
    try:
        if contact is None or contact is not None and not User.objects.filter(username=contact).exists():
            # If no contact is selected, render the inbox without any selected contact
            conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))#if you're not in conversation appears the contact and group chats list
            last_message_subquery = Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user),
                Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk'))
            ).order_by('-timestamp').values('timestamp')[:1]

            # Fetch the contacts with whom the user has conversations and annotate the last message timestamp for each
            contacts = User.objects.annotate(
            last_message_timestamp=Subquery(last_message_subquery)
            ).exclude(username=request.user.username).filter(
                Q(sent_messages__in=conversations) | Q(received_messages__in=conversations)
            ).order_by('-last_message_timestamp').distinct()
            print("here")
            return render(request, 'blog/chat2.html', {'group_chats':group_chats,'contacts': contacts,'message_type': message_type})
        
        conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)) #if you re in conversation appears the contact and group chats list
        last_message_subquery = Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user),
                Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk'))
            ).order_by('-timestamp').values('timestamp')[:1]

            # Fetch the contacts with whom the user has conversations and annotate the last message timestamp for each
        contacts = User.objects.annotate(
        last_message_timestamp=Subquery(last_message_subquery)
            ).exclude(username=request.user.username).filter(
                Q(sent_messages__in=conversations) | Q(received_messages__in=conversations)
            ).order_by('-last_message_timestamp').distinct()
        group_chats = GroupChat.objects.filter(members=request.user)
        print(group_chats)
        print(contacts)
        # Fetch all messages where the current user is either the sender or the recipient
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient__username=contact)) |
            (Q(sender__username=contact) & Q(recipient=request.user))
        ).order_by('timestamp')
        attachments = Attachment.objects.filter(message__in=messages)

        # Group messages by conversation (combination of sender and recipient)
        conversations = {} #rendering of messages(recipient and sender appears)
        for message in messages: #ftp
            if message.sender == request.user:
                other_user = message.recipient
            else:
                other_user = message.sender
            
            conversation_key = (request.user, other_user)

            if conversation_key not in conversations:
                conversations[conversation_key] = []
            try:
                decrypted_message_content = decrypt_message(message.content[2:len(message.content)-1]) #when saved in database it looses the byte form so you need to cut it from the end and begining to remove the ("")
                message.content = decrypted_message_content 
            except Exception as e: 
                # If decryption fails, log the error and set content to an error message
                message.content = "Decryption error: Unable to decrypt message content"
            message_attachments = attachments.filter(message=message)
            # Add the message to the conversation
            conversations[conversation_key].append({'group_chats':group_chats,'message': message, 'attachments': message_attachments, 'message_type': message_type})

        # Get the selected contact
        selected_contact = User.objects.get(username=contact)
        if selected_contact.profile.blocked_users.filter(username=request.user.username).exists():
            is_blocked = True
        else:
            is_blocked = False
        if request.session.get('scroll_to_bottom', False):
            # Clear the session variable
            del request.session['scroll_to_bottom']
            # Redirect to the same URL to trigger scrolling to bottom
            return redirect('inbox_with_contact', contact=contact)
        # Pass the selected contact's username to the template
        return render(request, 'blog/chat2.html', {
            'contacts': contacts,  # Pass the filtered contacts
            'group_chats': group_chats,
            'selected_contact': selected_contact,
            'selected_contact_username': selected_contact.username,  # Add this line
            'selected_conversation': conversations.get((request.user, selected_contact), []),
            'message_type': message_type,
            'is_blocked': is_blocked
        })

    except Exception as e:
        # Handle exceptions gracefully
        print(f"An unexpected error occurred: {e}")
        return render(request, 'blog/chat2.html', {'error': 'An unexpected error occurred. Please try again later.'})
   
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

def contactus(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            subject = f'New message from {name} {last_name}'
            body = f'From: {email}\n\n{message}'
            sender_email = 'your_email@example.com'
            recipient_email = ['firasbenhmida23@gmail.com']

            send_mail(subject, body, sender_email, recipient_email)

            messages.success(request, 'Your message has been sent successfully! Thanks for your feedback')

            # Check if the user is authenticated
            if request.user.is_authenticated:
                # Redirect to the home page if the user is logged in
                return redirect('chat')  # Replace 'home' with the URL name of your home page
            else:
                # Redirect to the login page if the user is not logged in
                return redirect('login')  # Replace 'login' with the URL name of your login page
        else:
            print(form.errors)
            return render(request, 'contact/contactus.html', {'form': form, 'error_message': 'Form is invalid'})
    else:
        form = ContactForm()
    
    return render(request, 'contact/contactus.html', {'form': form})

def success(request):
    return HttpResponse('success')



def create_group_chat(request):
    conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    last_message_subquery = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk'))
        ).order_by('-timestamp').values('timestamp')[:1]

        # Fetch the contacts and annotate the last message timestamp for each
    contacts = User.objects.annotate(
            last_message_timestamp=Subquery(last_message_subquery)
        ).exclude(username=request.user.username).order_by('-last_message_timestamp')
    group_chats = GroupChat.objects.filter(members=request.user)
    if request.method == 'POST':
        print("here in create group chat")
        
        form = GroupChatForm(request.POST)
        if form.is_valid():
            print("valid ngga")
            group_chat = form.save(commit=False)
            group_chat.owner = request.user
            group_chat.save()  # Save the group chat first
            # Now that the group chat is saved, you can add members to it
            form.save_m2m()  # This saves the many-to-many relationships
            # Add the current user as a member of the group chat
            group_chat.members.add(request.user)
            print(group_chat.members.all())
            # Optionally, add additional logic such as redirecting to the group chat page
            return redirect('inbox')  # Redirect to inbox or another page
    else:
        form = GroupChatForm()
    return render(request, 'blog/chat2.html', {'form': form, 'contacts':contacts,'group_chats':group_chats})  


def group_chat_inbox(request, group_chat_id=None):
    conversations = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    last_message_subquery = Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user),
                Q(sender=OuterRef('pk')) | Q(recipient=OuterRef('pk'))
            ).order_by('-timestamp').values('timestamp')[:1]

            # Fetch the contacts with whom the user has conversations and annotate the last message timestamp for each
    contacts = User.objects.annotate(
    last_message_timestamp=Subquery(last_message_subquery)
            ).exclude(username=request.user.username).filter(
                Q(sent_messages__in=conversations) | Q(received_messages__in=conversations)
            ).order_by('-last_message_timestamp').distinct()
    print("Sorted contacts:", contacts)
    message_type = "group"
    group_chats = GroupChat.objects.filter(members=request.user)
    owner = False
    profile = Profile.objects.get(user=request.user)
    try:
        if group_chat_id is None:
            # If no group chat is selected, render the inbox without any selected group chat
            group_chats = GroupChat.objects.filter(members=request.user)
            print(group_chats)
            return render(request, 'blog/chat2.html', {'group_chats': group_chats, 'contacts':contacts,'message_type': message_type})

        # Fetch the selected group chat
        selected_group_chat = GroupChat.objects.get(pk=group_chat_id)
        is_owner_or_admin = False
        if request.user == selected_group_chat.owner or request.user in selected_group_chat.administrators.all():
            is_owner_or_admin = True
        if request.user == selected_group_chat.owner :
            owner = True
        # Ensure that the current user is a member of the selected group chat
        if request.user not in selected_group_chat.members.all():
            return HttpResponseForbidden("You are not authorized to access this group chat.")

        # Fetch all messages in the selected group chat
        group_messages = GroupMessage.objects.filter(group_chat=selected_group_chat).order_by('timestamp')
        for message in group_messages:
            try:
                decrypted_message_content = decrypt_message(message.content[2:len(message.content)-1])
                message.content = decrypted_message_content 
            except Exception as e:
                # If decryption fails, log the error and set content to an error message
                message.content = "Decryption error: Unable to decrypt message content"
        print(selected_group_chat.picture)
        # Render the template with the selected group chat and its messages
        return render(request, 'blog/chat2.html', {
            'contacts':contacts,
            'group_chats':group_chats,
            'selected_group_chat': selected_group_chat,
            'group_messages': group_messages,
            'message_type': message_type,
            'admin':is_owner_or_admin,
            'owner': owner,
            'profile':profile
        })

    except GroupChat.DoesNotExist:
        # Handle the case where the selected group chat does not exist
        return render(request, 'blog/chat2.html', {'group_chats': group_chats, 'contacts':contacts,'message_type': message_type})
    except Exception as e:
        print("here?")
        # Handle other exceptions gracefully
        print(f"An unexpected error occurred: {e}")
        return render(request, 'blog/chat2.html', {'error': 'An unexpected error occurred. Please try again later.'})
    

def post_group_message(request):
    if request.method == 'POST':
        group_chat_id = request.POST.get('group_chat_id')
        print("here i am in the post of group")
        print("post", request.POST)
        message_content = request.POST.get('content', '')
        attachments = request.FILES.getlist('attachment', [])
        
        try:
            if not group_chat_id:
                raise ValueError("Group chat ID is empty")

            group_chat = GroupChat.objects.get(pk=group_chat_id)
            sender = request.user
            encrypted_content = encrypt_message(message_content)
            print("print",message_content)
            if message_content.strip():
                print("Here in strip")
                message = GroupMessage(sender=sender, content=encrypted_content, group_chat=group_chat)
                message.save()

                for attachment in attachments:
                    Attachmentg.objects.create(message=message, file=attachment)
                
                messages.success(request, 'Message sent successfully.')
                print("no existant" ,request.POST)
                # Return success response as JSON
                return JsonResponse({'success': True, 'message': "Message sent to  successfully."})
            else:
                messages.error(request, "Message content cannot be empty.")
        except GroupChat.DoesNotExist:
            messages.error(request, f"Group chat with ID {group_chat_id} does not exist.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
        
        # Return error response as JSON
        return JsonResponse({'success': False, 'error': 'Failed to send message.'})

    else:
        # Handle other HTTP methods (e.g., GET) gracefully
        return JsonResponse({'success': False, 'error': 'Method not allowed.'})
    
    
def delete_messageG(request, message_id):
    # Fetch the message object by its ID
    message = get_object_or_404(GroupMessage, pk=message_id)
    
    # Get the recipient username from the message
    recipient_username = message.group_chat
    
    # Check if the current user is the sender of the message
    if message.sender == request.user:
        # Delete the message
        message.delete()
        messages.success(request, 'Message deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this message.')
    
    # Redirect back to the inbox or conversation page
    return redirect('group_chat_inbox', group_chat_id=message.group_chat.id)

def handle_message(request):
    
    if request.method == 'POST':
        message_type = request.POST.get('message_types')
        
        if message_type == 'contact':
            print("Here in handle contact")
            # Process direct message
            return post_message(request)
        
        elif message_type == 'group':
            # Process group message
            
            return post_group_message(request)
        else:
            # Handle invalid message type
            return HttpResponseBadRequest("Invalid message type")
    else:
        
        # Handle other HTTP methods if necessary
        print("here")
        return HttpResponseNotAllowed(['POST'])
    

def group_chat_admin(request, group_chat_id):
    group_chat = get_object_or_404(GroupChat, pk=group_chat_id)
    
    # Check if the current user is the owner or an administrator of the group
    is_owner_or_admin = request.user == group_chat.owner or request.user in group_chat.administrators.all()
    
    if is_owner_or_admin:
        # Render the admin interface template
        return render(request, 'blog/group_chat_admin.html', {'group_chat': group_chat})
    else:
        # Redirect or display an error message if the user is not authorized
        return HttpResponseForbidden("You are not authorized to access this page.")
    

def add_user_to_group_chat(request):
    if request.method == 'POST':
        group_chat_id = request.POST.get('group_chat_id')
        username = request.POST.get('username')

        group_chat = get_object_or_404(GroupChat, pk=group_chat_id)

        # Check if the current user is the owner or an administrator of the group chat
        is_owner_or_admin = request.user == group_chat.owner or request.user in group_chat.administrators.all()
        if is_owner_or_admin:
            try:
                user_to_add = User.objects.get(username=username)
                group_chat.members.add(user_to_add)
                return redirect('group_chat_inbox', group_chat_id=group_chat_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'User with username {username} does not exist.'})
        else:
            return JsonResponse({'success': False, 'message': 'You are not authorized to perform this action.'})

@login_required
def remove_user_from_group_chat(request):
    if request.method == 'POST':
        group_chat_id = request.POST.get('group_chat_id')
        username = request.POST.get('username')

        group_chat = get_object_or_404(GroupChat, pk=group_chat_id)

        # Check if the current user is the owner or an administrator of the group chat
        is_owner_or_admin = request.user == group_chat.owner or request.user in group_chat.administrators.all()
        if is_owner_or_admin:
            try:
                user_to_remove = User.objects.get(username=username)
                group_chat.members.remove(user_to_remove)
                return redirect('group_chat_inbox', group_chat_id=group_chat_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'User with username {username} does not exist.'})
        else:
            return JsonResponse({'success': False, 'message': 'You are not authorized to perform this action.'})
        
def set_group_chat_picture(request):
    if request.method == 'POST':
        form = SetGroupChatPictureForm(request.POST, request.FILES)
        if form.is_valid():
            group_chat_id = request.POST.get('group_chat_id')
            picture = form.cleaned_data['picture']
            try:
                group_chat_id = request.POST.get('group_chat_id')
                group_chat = get_object_or_404(GroupChat, pk=group_chat_id)
                group_chat.picture = picture
                group_chat.save()
                messages.success(request, 'Group chat picture set successfully.')
            except GroupChat.DoesNotExist:
                messages.error(request, f'Group chat with ID {group_chat_id} does not exist.')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        messages.error(request, 'Invalid request method.')
    
    # Redirect back to the group chat inbox
    return redirect('group_chat_inbox')


def add_administrator_to_group_chat(request):
    if request.method == 'POST':
        group_chat_id = request.POST.get('group_chat_id')
        username = request.POST.get('admin_username')
        print("this is username")
        group_chat = get_object_or_404(GroupChat, pk=group_chat_id)

        # Check if the current user is the owner of the group chat
        is_owner = request.user == group_chat.owner
        if is_owner:
            try:
                print("going on")
                user_to_add = User.objects.get(username=username)
                print(user_to_add.username)
                group_chat.administrators.add(user_to_add)
                return redirect('group_chat_inbox', group_chat_id=group_chat_id)
            except User.DoesNotExist:
               
                return JsonResponse({'success': False, 'message': f'User with username {username} does not exist.'})
        else:
            return JsonResponse({'success': False, 'message': 'You are not authorized to perform this action.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
def change_group_name(request):
    if request.method == 'POST':
        group_chat_id = request.POST.get('group_chat_id')
        new_group_name = request.POST.get('new_group_name')

        group_chat = get_object_or_404(GroupChat, pk=group_chat_id)

        # Check if the current user is the owner of the group chat
        if request.user == group_chat.owner:
            group_chat.group_name = new_group_name
            group_chat.save()
            return redirect('group_chat_inbox', group_chat_id=group_chat_id)

        else:
            return JsonResponse({'success': False, 'message': 'You are not authorized to perform this action.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    

def index(request):
    return render(request, "test/index.html")