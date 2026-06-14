import shutil
import subprocess
import sys
from pathlib import Path


def create_archive(source_dir: Path, dest_file: Path, sevenzip_level: int = 2) -> Path:
    """Compress source_dir into a 7z/zip archive, or a DMG on macOS. Returns the created archive path."""
    dest_path = Path(dest_file)

    if sys.platform == 'darwin':
        archive_path = dest_path.with_suffix('.dmg')
        subprocess.run(
            [
                'hdiutil', 'create',
                '-volname', dest_path.name,
                '-srcfolder', str(source_dir),
                '-ov', '-format', 'UDZO',
                str(archive_path),
            ],
            check=True,
        )
        return archive_path

    if shutil.which('7z'):
        archive_path = dest_path.with_suffix('.7z')
        subprocess.run(
            ['7z', 'a', '-t7z', f'-mx={sevenzip_level}', str(archive_path), './*'],
            cwd=source_dir,
            check=True,
        )
    else:
        archive_path = Path(
            shutil.make_archive(base_name=str(dest_path), format='zip', root_dir=str(source_dir))
        )

    return archive_path
