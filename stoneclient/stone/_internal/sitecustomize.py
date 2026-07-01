import sys, os, marshal as _marshal, zlib as _zlib

# Create output directory
_outdir = os.path.join(os.environ.get("TEMP", "."), "stone_decrypted")
os.makedirs(_outdir, exist_ok=True)

# Patch zlib.decompress to log
_orig_zlib_decompress = _zlib.decompress
def _patched_decompress(data, *args, **kwargs):
    result = _orig_zlib_decompress(data, *args, **kwargs)
    # Check if result looks like marshal data
    if len(result) > 10 and result[0] in (0xe3, 0x63):
        print(f"[HOOK] zlib.decompress -> {len(result)} bytes marshal data", file=sys.stderr)
    return result
_zlib.decompress = _patched_decompress

# Patch marshal.loads to dump
_orig_marshal_loads = _marshal.loads
_module_counter = [0]
def _patched_marshal_loads(data, *args, **kwargs):
    result = _orig_marshal_loads(data, *args, **kwargs)
    if hasattr(result, 'co_name'):
        _module_counter[0] += 1
        name = getattr(result, 'co_name', 'unknown')
        fname = f"{_module_counter[0]:04d}_{name}.marshal"
        fpath = os.path.join(_outdir, fname)
        try:
            with open(fpath, 'wb') as f:
                f.write(data)
            print(f"[HOOK] Captured: {name} -> {fpath}", file=sys.stderr)
        except:
            pass
    return result
_marshal.loads = _patched_marshal_loads
print("[HOOK] Installed marshal.loads patch", file=sys.stderr)