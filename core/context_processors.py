from chat.models import Message, GroupMessage


def unread_messages_count(request):
    if request.user.is_authenticated:
        dm_unread = Message.objects.filter(receiver=request.user, is_read=False).count()
        group_unread = GroupMessage.objects.filter(
            group__members=request.user
        ).exclude(sender=request.user).exclude(read_by=request.user).count()
        return {'unread_messages_count': dm_unread + group_unread}
    return {'unread_messages_count': 0}
