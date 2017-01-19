# -*- mode: python -*-

block_cipher = None

data_files=[
    ('helper/config', 'helper/config'),
    ('helper/config/log.json', 'config'),
    ('helper/data/empty.txt', 'helper/data'),
    ('helper_ui/config', 'helper_ui/config'),
    ('helper_ui/static', 'helper_ui/static'),
    ('helper_ui/templates', 'helper_ui/templates')
]

a = Analysis(['main_script.py'],
             pathex=['C:\\Users\\PW-SMurphy\\workspace\\cl_helper'],
             binaries=[],
             datas=data_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='main_script',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main_script')
