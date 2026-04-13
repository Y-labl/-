# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('*.png', '.'),
        ('config', 'config'),
        ('core', 'core'),
    ],
    # 勿加入 paddleocr/easyocr/torch：会拖入 onnx，PyInstaller 在本机分析时常崩溃；程序实际只用 cv2+pytesseract
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'pygetwindow',
        'pyautogui',
        'pytesseract',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'torchvision',
        'torchaudio',
        'onnx',
        'onnxruntime',
        'tensorboard',
        'paddle',
        'paddleocr',
        'paddlex',
        'easyocr',
        'modelscope',
        'tensorflow',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='晶石购买助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # 必须用 windowed 引导程序(runw)；打包请用本 spec 且建议加 --clean，勿用「pyinstaller gui.py」默认会带控制台
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
