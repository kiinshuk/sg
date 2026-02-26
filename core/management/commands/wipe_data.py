from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Post, Profile, Like, Follow, Comment
from chat.models import Message, GroupChat, GroupMember, GroupMessage


class Command(BaseCommand):
    help = 'Wipe all user data, posts, media references from the database'

    def handle(self, *args, **kwargs):
        GroupMessage.objects.all().delete()
        GroupMember.objects.all().delete()
        GroupChat.objects.all().delete()
        Message.objects.all().delete()
        Like.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✅ All data wiped successfully.'))
