import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


_INFO_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>{executable}</string>
    <key>CFBundleIdentifier</key>
    <string>com.xcantloadx.{name}</string>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>CFBundleDisplayName</key>
    <string>{display_name}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>CFBundleVersion</key>
    <string>{version}</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
"""


def _create_macos_dmg(source_dir: Path, dest_file: Path, app_name: str) -> Path:
    """Create a macOS drag-to-Applications DMG installer from a PyInstaller COLLECT output."""
    archive_path = dest_file.with_suffix('.dmg')

    m = re.search(r'_v([^_]+)_', dest_file.stem)
    version = m.group(1) if m else '0.0.0'

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Wrap PyInstaller COLLECT output in a .app bundle
        app_bundle = tmp_path / f'{app_name}.app'
        contents = app_bundle / 'Contents'
        macos_dir = contents / 'MacOS'
        resources_dir = contents / 'Resources'
        macos_dir.mkdir(parents=True)
        resources_dir.mkdir()

        shutil.copytree(source_dir, macos_dir, dirs_exist_ok=True, symlinks=True)

        # PyInstaller's macOS bootloader hard-codes the search path for libpython as
        # Contents/Frameworks/, regardless of where COLLECT placed the file.
        frameworks_dir = contents / 'Frameworks'
        frameworks_dir.mkdir()
        internal_dir = macos_dir / '_internal'
        if internal_dir.exists():
            for dylib in internal_dir.glob('libpython*.dylib'):
                shutil.copy2(dylib, frameworks_dir / dylib.name)

        icon_src = Path.cwd() / 'assets' / f'{app_name}.icns'
        icon_plist = ''
        if icon_src.exists():
            shutil.copy2(icon_src, resources_dir / f'{app_name}.icns')
            icon_plist = f'\n    <key>CFBundleIconFile</key>\n    <string>{app_name}</string>'

        plist = _INFO_PLIST.format(
            executable=app_name,
            name=app_name,
            display_name=app_name,
            version=version,
        ).replace('</dict>', f'{icon_plist}\n</dict>')
        (contents / 'Info.plist').write_text(plist, encoding='utf-8')

        # Build DMG staging area: .app + symlink to /Applications
        staging = tmp_path / 'staging'
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
