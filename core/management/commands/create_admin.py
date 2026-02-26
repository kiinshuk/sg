from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile
import os


class Command(BaseCommand):
    help = 'Create superuser from env vars if not exists — safe to run every deploy'

    def handle(self, *args, **kwargs):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@snapgram.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin1234!')

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Admin "{username}" already exists — skipping.')
            return

        user = User.objects.create_superuser(username, email, password)
        Profile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created with password from env.'))
