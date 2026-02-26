from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ── Direct Messages ──────────────────────────────────────────
class Message(models.Model):
    sender   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content  = models.TextField(max_length=1000)
    is_read  = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username} → {self.receiver.username}: {self.content[:30]}'


# ── Group Chats ───────────────────────────────────────────────
class GroupChat(models.Model):
    name       = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    avatar     = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    creator    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    members    = models.ManyToManyField(User, through='GroupMember', related_name='group_chats')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def last_message(self):
        return self.group_messages.order_by('-created_at').first()

    def unread_count(self, user):
        return self.group_messages.exclude(sender=user).filter(
            read_by__isnull=True
        ).count()


class GroupMember(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member')]
    group  = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='memberships')
    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role   = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f'{self.user.username} in {self.group.name}'


class GroupMessage(models.Model):
    group    = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='group_messages')
    sender   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_sent')
    content  = models.TextField(max_length=1000)
    read_by  = models.ManyToManyField(User, related_name='read_group_messages', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.group.name}] {self.sender.username}: {self.content[:30]}'
