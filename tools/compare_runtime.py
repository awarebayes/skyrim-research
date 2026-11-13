"""Ordinary functions with independently verified CRT termination actions.

The archived v2 and internal engines remain unchanged. This engine uses the ordinary v2
identity and boundaries, with the internal engine's complete import-thunk proof for the one
compiler runtime action it supports. Reports have a distinct, fully pinned engine identity.
"""
import hashlib
import importlib.util
from pathlib import Path

import compare as legacy
from compare_internal import InternalFunction, runtime_import_slot
from pecoff import SCN_MEM_EXECUTE, Reject

COMPARATOR_VERSION = '0.6.1-runtime'
CONTRACT_VERSION = legacy.CONTRACT_VERSION
REPORT_SCHEMA = legacy.REPORT_SCHEMA


def comparator_source_sha256():
    digest = hashlib.sha256()
    for name in ('compare.py', 'pecoff.py', 'compare_internal.py', 'source_digest.py', 'compare_runtime.py'):
        digest.update(name.encode() + b'\0' + Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


class RuntimeFunction(InternalFunction):
    # Keep ordinary external identity, references and primary boundaries. Only ref_field's
    # verified termination-action branch is shared with the internal engine.
    resolve = legacy.Function.resolve
    secrel_field = legacy.Function.secrel_field
    compare_unwind = legacy.Function.compare_unwind


# Load an independent instance so configuring this engine never changes the archived engine
# used to reproduce existing records, including when both are used in the same process.
_spec = importlib.util.spec_from_file_location('_ordinary_runtime_base', Path(legacy.__file__))
_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)
_engine.Function = RuntimeFunction
_engine.COMPARATOR_VERSION = COMPARATOR_VERSION
_engine.comparator_source_sha256 = comparator_source_sha256
compare = _engine.compare
main = _engine.main


def termination_thunk(image):
    """Find the unique complete indirect jump to the image's named termination import."""
    import struct
    slot = runtime_import_slot(image)
    found = []
    for section in image.sections:
        if not section.flags & SCN_MEM_EXECUTE:
            continue
        size = min(section.raw_size, section.vsize or section.raw_size)
        if not size:
            continue
        data = image.read(section.vaddr, size, 'runtime thunk search')[1]
        at = data.find(bytes((0xFF, 0x25)))
        while at >= 0:
            if at + 6 <= len(data):
                address = section.vaddr + at
                if address + 6 + struct.unpack_from('<i', data, at + 2)[0] == slot:
                    found.append(address)
            at = data.find(bytes((0xFF, 0x25)), at + 1)
    if len(found) != 1:
        raise Reject('eh-runtime-import', 'termination import needs exactly one complete import thunk')
    return {'rva': found[0], 'size': 6}


if __name__ == '__main__':
    raise SystemExit(main())
