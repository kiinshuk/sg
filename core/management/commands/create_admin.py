from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile
import os


class Command(BaseCommand):
    help = 'Create superuser from env vars if not exists'

    def handle(self, *args, **kwargs):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@snapgram.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin1234!')

        self.stdout.write(f'Checking for superuser: {username}')
        self.stdout.write(f'Total users in DB: {User.objects.count()}')

        try:
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                if not user.is_superuser:
                    user.is_superuser = True
                    user.is_staff = True
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Upgraded "{username}" to superuser.'))
                else:
                    self.stdout.write(f'✅ Superuser "{username}" already exists.')
            else:
                user = User.objects.create_superuser(username, email, password)
                Profile.objects.get_or_create(user=user)
                self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created! Password: {password}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating superuser: {e}'))
