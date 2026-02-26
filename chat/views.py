from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q, Max, OuterRef, Subquery
from datetime import timezone, datetime
from .models import Message, GroupChat, GroupMember, GroupMessage
from core.models import Follow


# ── helpers ──────────────────────────────────────────────────
def get_connected_users(user):
    following = Follow.objects.filter(follower=user).values_list('following', flat=True)
    followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
    ids = set(list(following) + list(followers))
    return User.objects.filter(id__in=ids).select_related('profile')


# ── Inbox ─────────────────────────────────────────────────────
@login_required
def inbox(request):
    connected = get_connected_users(request.user)

    # Build DM conversations
    dm_convos = []
    for other in connected:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver=other) |
            Q(sender=other, receiver=request.user)
        ).order_by('-created_at').first()
        unread = Message.objects.filter(sender=other, receiver=request.user, is_read=False).count()
        dm_convos.append({'user': other, 'last_message': last_msg, 'unread': unread, 'type': 'dm'})

    # ✅ FIXED: Use datetime.min and timezone.utc
    dm_convos.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # Build group conversations
    user_groups = GroupChat.objects.filter(members=request.user).prefetch_related('members', 'memberships')
    group_convos = []
    for grp in user_groups:
        last_msg = grp.last_message()
        unread = GroupMessage.objects.filter(group=grp).exclude(sender=request.user).exclude(read_by=request.user).count()
        group_convos.append({'group': grp, 'last_message': last_msg, 'unread': unread, 'type': 'group'})

    # ✅ FIXED: Same fix here
    group_convos.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # Merge and sort all conversations
    all_convos = []
    for d in dm_convos:
        # ✅ FIXED: And here
        all_convos.append({**d, 'sort_key': d['last_message'].created_at if d['last_message'] else datetime.min.replace(tzinfo=timezone.utc)})
    for g in group_convos:
        # ✅ FIXED: And here
        all_convos.append({**g, 'sort_key': g['last_message'].created_at if g['last_message'] else datetime.min.replace(tzinfo=timezone.utc)})
    all_convos.sort(key=lambda x: x['sort_key'], reverse=True)

    return render(request, 'chat/inbox.html', {
        'all_convos': all_convos,
        'connected_users': connected,
    })

    
# ── Direct Messages ───────────────────────────────────────────
@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=request.user, following=other_user).exists()
    follower  = Follow.objects.filter(follower=other_user, following=request.user).exists()
    if not (following or follower):
        return redirect('inbox')

    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)
        return redirect('conversation', username=username)

    connected = get_connected_users(request.user)
    return render(request, 'chat/conversation.html', {
        'other_user': other_user,
        'messages': msgs,
        'connected_users': connected,
        'chat_type': 'dm',
    })


@login_required
def send_message_ajax(request, username):
    if request.method == 'POST':
        other_user = get_object_or_404(User, username=username)
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(sender=request.user, receiver=other_user, content=content)
            return JsonResponse({
                'status': 'ok', 'id': msg.id,
                'message': msg.content,
                'sender': request.user.username,
                'time': msg.created_at.strftime('%I:%M %p'),
            })
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_messages_ajax(request, username):
    other_user = get_object_or_404(User, username=username)
    after_id = int(request.GET.get('after', 0))
    msgs = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user),
        id__gt=after_id
    ).order_by('created_at')
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    data = [{'id': m.id, 'content': m.content, 'sender': m.sender.username,
              'time': m.created_at.strftime('%I:%M %p'), 'is_me': m.sender == request.user} for m in msgs]
    return JsonResponse({'messages': data})


# ── Group Chats ───────────────────────────────────────────────
@login_required
def create_group(request):
    connected = get_connected_users(request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        member_ids = request.POST.getlist('members')
        if not name:
            django_messages.error(request, 'Group name is required.')
            return render(request, 'chat/create_group.html', {'connected_users': connected})

        group = GroupChat.objects.create(name=name, description=description, creator=request.user)
        # Add creator as admin
        GroupMember.objects.create(group=group, user=request.user, role='admin')
        # Add selected members
        for uid in member_ids:
            try:
                u = User.objects.get(id=uid)
                if u != request.user:
                    GroupMember.objects.get_or_create(group=group, user=u, defaults={'role': 'member'})
            except User.DoesNotExist:
                pass
        # Handle avatar
        if request.FILES.get('avatar'):
            group.avatar = request.FILES['avatar']
            group.save()
        django_messages.success(request, f'Group "{name}" created!')
        return redirect('group_conversation', group_id=group.id)

    return render(request, 'chat/create_group.html', {'connected_users': connected})


@login_required
def group_conversation(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if not group.members.filter(id=request.user.id).exists():
        return redirect('inbox')

    # Mark messages as read
    unread_msgs = GroupMessage.objects.filter(group=group).exclude(sender=request.user).exclude(read_by=request.user)
    for msg in unread_msgs:
        msg.read_by.add(request.user)

    msgs = GroupMessage.objects.filter(group=group).select_related('sender', 'sender__profile').order_by('created_at')
    members = group.memberships.select_related('user', 'user__profile')
    connected = get_connected_users(request.user)
    user_membership = group.memberships.filter(user=request.user).first()

    return render(request, 'chat/group_conversation.html', {
        'group': group,
        'messages': msgs,
        'members': members,
        'connected_users': connected,
        'chat_type': 'group',
        'user_membership': user_membership,
    })


@login_required
def send_group_message(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(GroupChat, id=group_id)
        if not group.members.filter(id=request.user.id).exists():
            return JsonResponse({'status': 'error'}, status=403)
        content = request.POST.get('content', '').strip()
        if content:
            msg = GroupMessage.objects.create(group=group, sender=request.user, content=content)
            msg.read_by.add(request.user)
            avatar_url = request.user.profile.profile_pic.url if request.user.profile.profile_pic else None
            return JsonResponse({
                'status': 'ok', 'id': msg.id,
                'content': msg.content,
                'sender': request.user.username,
                'time': msg.created_at.strftime('%I:%M %p'),
                'avatar': avatar_url,
            })
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_group_messages(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if not group.members.filter(id=request.user.id).exists():
        return JsonResponse({'status': 'error'}, status=403)
    after_id = int(request.GET.get('after', 0))
    msgs = GroupMessage.objects.filter(group=group, id__gt=after_id).select_related('sender', 'sender__profile').order_by('created_at')
    for msg in msgs:
        msg.read_by.add(request.user)
    data = [{
        'id': m.id, 'content': m.content,
        'sender': m.sender.username,
        'time': m.created_at.strftime('%I:%M %p'),
        'is_me': m.sender == request.user,
        'avatar': m.sender.profile.profile_pic.url if m.sender.profile.profile_pic else None,
    } for m in msgs]
    return JsonResponse({'messages': data})


@login_required
def add_group_member(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    membership = group.memberships.filter(user=request.user, role='admin').first()
    if not membership:
        return JsonResponse({'status': 'error', 'message': 'Only admins can add members'}, status=403)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            GroupMember.objects.get_or_create(group=group, user=user, defaults={'role': 'member'})
            return JsonResponse({'status': 'ok', 'username': user.username})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def remove_group_member(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    membership = group.memberships.filter(user=request.user, role='admin').first()
    if not membership:
        return JsonResponse({'status': 'error'}, status=403)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        GroupMember.objects.filter(group=group, user_id=user_id).delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if request.method == 'POST':
        GroupMember.objects.filter(group=group, user=request.user).delete()
        django_messages.success(request, f'You left "{group.name}".')
        return redirect('inbox')
    return redirect('group_conversation', group_id=group_id)
