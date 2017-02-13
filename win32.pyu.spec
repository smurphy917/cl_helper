# -*- mode: python -*-
import os, inspect, pyupdater

block_cipher = None

data_files=[
    ('helper/config', 'helper/config'),
    ('helper_ui/static', 'helper_ui/static'),
    ('helper_ui/templates', 'helper_ui/templates'),
    ('drivers','drivers'),
    ('logo.ico','.'),
    ('config','config')
]

a = Analysis([os.path.join(os.path.dirname(inspect.stack()[0][1]),'main_script.py')],
             pathex=[os.path.dirname(inspect.stack()[0][1])],
             binaries=[],
             datas=data_files,
             hiddenimports=[],
             hookspath=[os.path.join(os.path.dirname(pyupdater.__file__),'hooks')],
             runtime_hooks=[],
             excludes=['jinja2.asyncsupport', 'jinja2.asyncfilters'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='win',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='logo.ico'
          )
