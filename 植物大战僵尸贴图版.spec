# plant-vs-zombies.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['D:\pycharm\pvz'],
    binaries=[],
    datas=[
        ('rsc_mng', 'rsc_mng'),
        ('plants', 'plants'),
        ('zombies', 'zombies'),
        ('animation', 'animation'),
        ('database', 'database'),
        ('ui', 'ui'),
        ('shop', 'shop'),
        ('bullets', 'bullets'),
        ('core', 'core'),
        ('save','save'),
        ('*.py', '.')

    ],
    hiddenimports=[
        'plants',
        'zombies',
        'animation',
        'database',
        'ui',
        'core',
        'bullets',
        'shop',
        'rsc_mng',
        'plants.base_plant',
        'zombies.base_zombie',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='植物大战僵尸贴图版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台

)