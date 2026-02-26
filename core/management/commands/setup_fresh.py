from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Post, Profile, Like, Follow, Comment
from chat.models import Message, GroupChat, GroupMember, GroupMessage
import os


class Command(BaseCommand):
    help = 'Wipe all data and create superuser from env vars (run once on fresh deploy)'

    def handle(self, *args, **kwargs):
        # Only run if FRESH_SETUP env var is set to 'true'
        if os.environ.get('FRESH_SETUP', '').lower() != 'true':
            self.stdout.write('Skipping fresh setup (FRESH_SETUP != true)')
            return

        self.stdout.write('Wiping all data...')
        GroupMessage.objects.all().delete()
        GroupMember.objects.all().delete()
        GroupChat.objects.all().delete()
        Message.objects.all().delete()
        Like.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✅ All data wiped.'))

        # Create superuser from env vars
        admin_user = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@snapgram.com')
        admin_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin1234')

        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(admin_user, admin_email, admin_pass)
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{admin_user}" created.'))
        else:
            self.stdout.write(f'Superuser "{admin_user}" already exists.')

        # Disable fresh setup after running once
        self.stdout.write(self.style.WARNING('⚠️  Now remove FRESH_SETUP from Railway Variables to prevent wiping on next deploy!'))
