import sys

from tools.build import BuildConfig
from tools.build.cli import main

_extra_hidden_imports: list[str] = []
if sys.platform == 'win32':
    _extra_hidden_imports.append('plyer.platforms.win.notification')
elif sys.platform == 'darwin':
    _extra_hidden_imports.append('plyer.platforms.macosx.notification')

CONFIG = BuildConfig(
    name='iaa',
    collect_packages=['kaa'],
    extra_hidden_imports=_extra_hidden_imports,
    runtime_copy=[
        ('assets', 'assets'),
        ('iaa/res', 'assets/res_compiled'),
    ],
)

if __name__ == '__main__':
    main(CONFIG)
