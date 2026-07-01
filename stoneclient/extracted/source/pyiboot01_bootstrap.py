# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: PyInstaller\loader\pyiboot01_bootstrap.py
# Compiled at: 2026-07-01 00:51:12
# Size of source mod 2**32: 859 bytes
import sys, pyimod02_importers
pyimod02_importers.install()
import os
if not hasattr(sys, "frozen"):
    sys.frozen = True
sys.prefix = sys._MEIPASS
sys.exec_prefix = sys.prefix
sys.base_prefix = sys.prefix
sys.base_exec_prefix = sys.exec_prefix
VIRTENV = "VIRTUAL_ENV"
if VIRTENV in os.environ:
    os.environ[VIRTENV] = ""
    del os.environ[VIRTENV]
python_path = []
for pth in sys.path:
    python_path.append(os.path.abspath(pth))
    sys.path = python_path
else:
    try:
        import encodings
    except ImportError:
        pass
    else:
        if sys.warnoptions:
            import warnings
        import pyimod03_ctypes
        pyimod03_ctypes.install()
        if sys.platform.startswith("win"):
            import pyimod04_pywin32
            pyimod04_pywin32.install()
        for entry in os.listdir(sys._MEIPASS):
            entry = os.path.join(sys._MEIPASS, entry)

        if not os.path.isdir(entry):
            pass
        elif entry.endswith(".egg"):
            sys.path.append(entry)
