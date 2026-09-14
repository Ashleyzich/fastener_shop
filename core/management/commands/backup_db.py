import os
import shutil
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Create a backup of the database'

    def handle(self, *args, **options):
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_file)
        
        # Database file path
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            self.stdout.write(self.style.SUCCESS(f'✓ Backup created: {backup_file}'))
        else:
            self.stdout.write(self.style.ERROR('Database file not found!'))
