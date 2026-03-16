from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError

User = get_user_model()

class Command(BaseCommand):
    help = "Custom superuser creation (email-only, username auto-assigned)"

    def handle(self, *args, **options):
        # Custom banner
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== CUSTOM SUPERUSER CREATION ==="))
        self.stdout.write(self.style.NOTICE("This script asks only for email, username auto-assigned.\n"))

        email = options.get('email')
        if not email:
            email = input("Email: ").strip()

        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email '{email}' already exists.")

        # Auto-assign username = email
        options['username'] = email

        # Remove email from REQUIRED_FIELDS to avoid double prompt
        if hasattr(User, 'REQUIRED_FIELDS') and 'email' in User.REQUIRED_FIELDS:
            User.REQUIRED_FIELDS = [f for f in User.REQUIRED_FIELDS if f != 'email']

        # Call original handle to get the user instance
        # Override user creation to manually set email
        password = options.get('password')  # None if interactive
        interactive = options.get('interactive', True)

        if interactive and not password:
            # let BaseCommand handle password prompt
            super().handle(*args, **options)
            # fetch the last created superuser and set email manually
            user = User.objects.filter(username=email).first()
            if user:
                user.email = email
                user.save()
        else:
            # Non-interactive, create user manually
            user = User.objects.create_superuser(username=email, email=email, password=password)

        self.stdout.write(self.style.SUCCESS("Custom superuser created successfully!"))