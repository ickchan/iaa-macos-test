import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _create_macos_dmg(source_dir: Path, dest_file: Path, app_name: str) -> Path:
    """Create a macOS drag-to-Applications DMG from a directory containing a .app bundle."""
    archive_path = dest_file.with_suffix('.dmg')
    app_bundle = source_dir / f'{app_name}.app'

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / 'staging'
        staging.mkdir()
        shutil.copytree(app_bundle, staging / app_bundle.name, symlinks=True)
        (staging / 'Applications').symlink_to('/Applications')

        subprocess.run(
            [
                'hdiutil', 'create',
                '-volname', app_name,
                '-srcfolder', str(staging),
                '-ov', '-format', 'UDZO',
                str(archive_path),
            ],
            check=True,
        )

    return archive_path


def create_archive(
    source_dir: Path,
    dest_file: Path,
    sevenzip_level: int = 2,
    app_name: str = 'app',
) -> Path:
    """Compress source_dir. On macOS produces a drag-to-Applications DMG; elsewhere 7z or zip."""
    dest_path = Path(dest_file)

    if sys.platform == 'darwin':
        return _create_macos_dmg(source_dir, dest_path, app_name)

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
