# -*- mode: python -*-

block_cipher = None

data_files=[
    ('helper/config', 'helper/config'),
    ('helper/data/empty.txt', 'helper/data'),
    ('helper_ui/config', 'helper_ui/config'),
    ('helper_ui/static', 'helper_ui/static'),
    ('helper_ui/templates', 'helper_ui/templates'),
    ('drivers','drivers'),
    ('logo.ico','.'),
    ('config','config')
]

a = Analysis(['C:\\Users\\PW-SMurphy\\workspace\\cl_helper\\main_script.py'],
             pathex=['C:\\Users\\PW-SMurphy\\workspace\\cl_helper', 'C:\\Users\\PW-SMurphy\\workspace\\cl_helper'],
             binaries=[],
             datas=data_files,
             hiddenimports=[],
             hookspath=['c:\\users\\pw-smurphy\\appdata\\local\\programs\\python\\python35-32\\lib\\site-packages\\pyupdater\\hooks'],
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
