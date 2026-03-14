#!/usr/bin/env python
"""
===========================================
Database Backup Script
===========================================
Creates timestamped MySQL database backups.

Usage:
    python scripts/backup.py

Set BACKUP_DIR in .env to configure backup location.
Requires `mysqldump` to be available in the system PATH.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings
from decouple import config


def backup_database():
    """Create a timestamped database backup using mysqldump."""
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = config('DB_NAME', default='school_fms')
    db_user = config('DB_USER', default='root')
    db_password = config('DB_PASSWORD', default='')
    db_host = config('DB_HOST', default='127.0.0.1')
    db_port = config('DB_PORT', default='3306')

    backup_file = backup_dir / f'{db_name}_{timestamp}.sql'

    cmd = [
        'mysqldump',
        f'--host={db_host}',
        f'--port={db_port}',
        f'--user={db_user}',
        f'--result-file={backup_file}',
        '--single-transaction',
        '--routines',
        '--triggers',
        db_name,
    ]

    if db_password:
        cmd.insert(4, f'--password={db_password}')

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f'✅ Backup created: {backup_file}')
        print(f'   Size: {backup_file.stat().st_size / 1024:.1f} KB')

        # Cleanup old backups (keep last 10)
        backups = sorted(backup_dir.glob(f'{db_name}_*.sql'), reverse=True)
        for old_backup in backups[10:]:
            old_backup.unlink()
            print(f'   🗑️  Removed old backup: {old_backup.name}')

    except subprocess.CalledProcessError as e:
        print(f'❌ Backup failed: {e.stderr}')
        sys.exit(1)
    except FileNotFoundError:
        print('❌ mysqldump not found. Please install MySQL client tools.')
        sys.exit(1)


if __name__ == '__main__':
    backup_database()
