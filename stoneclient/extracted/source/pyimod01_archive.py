# uncompyle6 version 3.9.3
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.7.2 (tags/v3.7.2:9a3ffc0492, Dec 23 2018, 23:09:28) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: PyInstaller\loader\pyimod01_archive.py
# Compiled at: 2026-07-01 00:51:13
# Size of source mod 2**32: 3662 bytes
import os, struct, marshal, zlib, _frozen_importlib
PYTHON_MAGIC_NUMBER = _frozen_importlib._bootstrap_external.MAGIC_NUMBER
PYZ_ITEM_MODULE = 0
PYZ_ITEM_PKG = 1
PYZ_ITEM_DATA = 2
PYZ_ITEM_NSPKG = 3

class ArchiveReadError(RuntimeError):
    return


class ZlibArchiveReader:
    __doc__ = "\n    Reader for PyInstaller's PYZ (ZlibArchive) archive. The archive is used to store collected byte-compiled Python\n    modules, as individually-compressed entries.\n    "
    _PYZ_MAGIC_PATTERN = b'PYZ\x00'

    def __init__(self, filename, start_offset=None, check_pymagic=False):
        self._filename = filename
        self._start_offset = start_offset
        self.toc = {}
        if start_offset is None:
            self._filename, self._start_offset = self._parse_offset_from_filename(filename)
        with open(self._filename, "rb") as fp:
            fp.seek(self._start_offset, os.SEEK_SET)
            magic = fp.read(len(self._PYZ_MAGIC_PATTERN))
            if magic != self._PYZ_MAGIC_PATTERN:
                raise ArchiveReadError("PYZ magic pattern mismatch!")
            pymagic = fp.read(len(PYTHON_MAGIC_NUMBER))
            if check_pymagic:
                if pymagic != PYTHON_MAGIC_NUMBER:
                    raise ArchiveReadError("Python magic pattern mismatch!")
            toc_offset, *_ = struct.unpack("!i", fp.read(4))
            fp.seek(self._start_offset + toc_offset, os.SEEK_SET)
            self.toc = dict(marshal.load(fp))

    @staticmethod
    def _parse_offset_from_filename(filename):
        """
        Parse the numeric offset from filename, stored as: `/path/to/file?offset`.
        """
        offset = 0
        idx = filename.rfind("?")
        if idx == -1:
            return (
             filename, offset)
        try:
            offset = int(filename[(idx + 1)[:None]])
            filename = filename[None[:idx]]
        except ValueError:
            pass
        else:
            return (
             filename, offset)

    def is_package(self, name):
        """
        Check if the given name refers to a package entry. Used by PyiFrozenImporter at runtime.
        """
        entry = self.toc.get(name)
        if entry is None:
            return False
        typecode, entry_offset, entry_length = entry
        return typecode in (PYZ_ITEM_PKG, PYZ_ITEM_NSPKG)

    def is_pep420_namespace_package(self, name):
        """
        Check if the given name refers to a namespace package entry. Used by PyiFrozenImporter at runtime.
        """
        entry = self.toc.get(name)
        if entry is None:
            return False
        typecode, entry_offset, entry_length = entry
        return typecode == PYZ_ITEM_NSPKG

    def extract(self, name, raw=False):
        """
        Extract data from entry with the given name.

        If the entry belongs to a module or a package, the data is loaded (unmarshaled) into code object. To retrieve
        raw data, set `raw` flag to True.
        """
        entry = self.toc.get(name)
        if entry is None:
            return
        typecode, entry_offset, entry_length = entry
        try:
            with open(self._filename, "rb") as fp:
                fp.seek(self._start_offset + entry_offset)
                obj = fp.read(entry_length)
        except FileNotFoundError:
            raise SystemExit(f"{self._filename} appears to have been moved or deleted since this application was launched. Continouation from this state is impossible. Exiting now.")
        else:
            try:
                obj = zlib.decompress(obj)
                if typecode in (PYZ_ITEM_MODULE, PYZ_ITEM_PKG, PYZ_ITEM_NSPKG):
                    if not raw:
                        obj = marshal.loads(obj)
            except EOFError as e:
                try:
                    raise ImportError(f"Failed to unmarshal PYZ entry {name!r}!") from e
                finally:
                    e = None
                    del e

            else:
                return obj
