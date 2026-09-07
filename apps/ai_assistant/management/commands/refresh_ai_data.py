from django.core.management.base import BaseCommand
from apps.ai_assistant.data_loader import refresh_ai_data

class Command(BaseCommand):
    help = 'Refresh AI assistant data cache'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Refreshing AI data...")
        refresh_ai_data()
        self.stdout.write(self.style.SUCCESS("✅ AI data refreshed successfully!"))