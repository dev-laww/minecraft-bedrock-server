import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
BACKUP_DIR = DATA_DIR / 'backups'


def create_backup():
    now = datetime.now()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    world_dir = DATA_DIR / Path('worlds') / 'Bedrock Level'
    world_zip = BACKUP_DIR / f'world_backup_{now.strftime("%Y%m%d_%H%M%S")}.mcworld'

    with zipfile.ZipFile(world_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in world_dir.rglob('*'):
            archive_name = file_path.relative_to(world_dir)
            zf.write(file_path, archive_name)

    return world_zip


def backup_every_interval(interval: int, stop_event: threading.Event):
    while not stop_event.is_set():
        create_backup()
        time.sleep(interval)


if __name__ == '__main__':
    create_backup()
    print(f'Backup created at {BACKUP_DIR}')
