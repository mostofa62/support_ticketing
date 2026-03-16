from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Create default roles: Staff and Client"

    def handle(self, *args, **kwargs):
        roles = ["Staff", "Client"]
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Role "{role}" created successfully!'))
            else:
                self.stdout.write(self.style.WARNING(f'Role "{role}" already exists.'))