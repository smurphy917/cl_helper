# -*- mode: python -*-

block_cipher = None


a = Analysis(['/Users/smurphy917/proj/cl_helper/main_script.py'],
             pathex=['/Users/smurphy917/proj/cl_helper', '/Users/smurphy917/proj/cl_helper'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['/Users/smurphy917/miniconda3/lib/python3.5/site-packages/pyupdater/hooks'],
             runtime_hooks=[],
             excludes=[],
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
          name='mac',
          debug=False,
          strip=False,
          upx=True,
          console=True )
