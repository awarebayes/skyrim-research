"""Opt-in internal-function comparison, contract v3; contract v2 stays unchanged.

Shares the byte, relocation, unwind and EH implementation with compare.py. Only TU-bound
identity, local reference names and stricter primary-section boundaries extend that contract.
"""
import argparse
import base64
import hashlib
import json
import struct
from pathlib import Path
import sys

from compare import (ROOT, TLS_INDEX, Function, check_placement, check_provenance,
                     check_relocation_layout, check_task, check_tls, code_section_sha256,
                     is_hash, is_text, is_uint, load_symbol_map, need, sanitized, sha256, write_diagnostics)
from pecoff import (SCN_CNT_CODE, SCN_MEM_EXECUTE, STORAGE_EXTERNAL, STORAGE_STATIC, UNW_FLAG_CHAININFO,
                    CoffObject, PeImage, Reject, Symbol, SYM_UNDEFINED)
from source_digest import DIGEST_METHOD

COMPARATOR_VERSION = '0.7.1-internal-prototype'
CONTRACT_VERSION = 3
REPORT_SCHEMA = 2
SELECTOR_FIELDS = {'symbol_type', 'storage_class', 'section_number', 'section_name', 'entry_offset'}
IDENTITY_FIELDS = SELECTOR_FIELDS | {'identity_schema', 'source_digest_method', 'source_revision',
                                     'source_path', 'object_sha256', 'map_key'}


def comparator_source_sha256():
    digest = hashlib.sha256()
    for name in ('compare.py', 'pecoff.py', 'compare_internal.py', 'source_digest.py'):
        digest.update(name.encode() + b'\0' + Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def runtime_import_slot(image):
    """The unique unbound VCRUNTIME140 import of the compiler's termination action.

    This is a CRT dependency, not a candidate funclet. Its identity must come from the image's
    import structures; the map alone cannot turn an arbitrary action into a runtime dependency.
    Bound imports, ordinal imports for this action, missing names and ambiguous slots refuse.
    """
    reason = 'eh-runtime-import'
    blob = image.blob
    opt = struct.unpack_from('<I', blob, 60)[0] + 24
    count = struct.unpack_from('<I', blob, opt + 108)[0]
    need(count > 1, reason, 'termination action needs an import directory')
    directory, size = struct.unpack_from('<II', blob, opt + 120)
    need(directory and 20 <= size <= 20 * 4096 and size % 20 == 0, reason,
         'termination action needs bounded import descriptors')

    def string(rva):
        raw = bytearray()
        for i in range(256):
            value = image.read(rva + i, 1, 'runtime import string')[1][0]
            if value == 0:
                need(all(32 <= c < 127 for c in raw), reason, 'runtime import name is not ASCII')
                return raw.decode('ascii')
            raw.append(value)
        raise Reject(reason, 'runtime import name is unterminated')

    matches, terminated = [], False
    for i in range(size // 20):
        fields = struct.unpack('<5I', image.read(directory + 20 * i, 20, 'import descriptor')[1])
        if not any(fields):
            terminated = True
            break
        original, timestamp, _forward, name, iat = fields
        if string(name).lower() != 'vcruntime140.dll':
            continue
        need(original and iat and timestamp == 0, reason, 'bound or nameless runtime imports are unsupported')
        ended = False
        for j in range(4096):
            entry = struct.unpack('<Q', image.read(original + 8 * j, 8, 'runtime import lookup')[1])[0]
            slot = iat + 8 * j
            stored = struct.unpack('<Q', image.read(slot, 8, 'runtime import address')[1])[0]
            need(stored == entry, reason, 'runtime IAT differs from its unbound lookup table')
            if entry == 0:
                ended = True
                break
            if entry & (1 << 63):
                continue
            need(entry <= 0xFFFFFFFF, reason, 'runtime import name is not an RVA')
            if string(entry + 2) == '__std_terminate':
                matches.append(slot)
        need(ended, reason, 'runtime import lookup is unterminated')
    need(terminated and len(matches) == 1, reason, 'termination action needs exactly one named runtime import')
    return matches[0]


def selector(obj, sym):
    return {'symbol_type': sym.kind, 'storage_class': sym.storage, 'section_number': sym.section,
            'section_name': obj.section(sym.section).name, 'entry_offset': sym.value}


def check_selector(value):
    need(isinstance(value, dict) and set(value) == SELECTOR_FIELDS, 'invalid-task',
         'internal selector has missing or unknown fields')
    need(all(type(value[k]) is int for k in SELECTOR_FIELDS - {'section_name'})
         and value['storage_class'] == STORAGE_STATIC and value['symbol_type'] == 0x20
         and is_uint(value['section_number']) and value['section_number'] > 0
         and is_text(value['section_name']) and value['entry_offset'] == 0,
         'candidate-boundary-unsupported', 'internal selector must name a section-start static function')


def local_key(source_revision, source_path, name, value):
    """Source digest includes repository paths; section identity distinguishes repeated local names.

    Object hashes deliberately stay outside map keys: the two clean host objects differ, but
    each task pins its own complete object separately. No symbol-table index enters the key.
    """
    payload = json.dumps([source_revision, source_path, name, value], sort_keys=True).encode()
    encoded = base64.b32encode(hashlib.sha256(payload).digest()).decode().rstrip('=').lower()
    return 'local-' + '-'.join(encoded[i:i + 8] for i in range(0, len(encoded), 8))


def symbol_key(obj, sym, task):
    if sym.storage == STORAGE_STATIC and sym.section > 0:
        return local_key(task['source_revision'], task['source_path'], sym.name, selector(obj, sym))
    return sym.name


def make_identity(obj_bytes, name, value, revision, path):
    check_selector(value)
    return dict(value, identity_schema=1, source_digest_method=DIGEST_METHOD, source_revision=revision,
                source_path=path, object_sha256=sha256(obj_bytes),
                map_key=local_key(revision, path, name, value))


def check_internal_identity(task):
    need(task.get('task_schema') == 2, 'invalid-task', 'internal function needs task_schema 2')
    ident = task.get('internal_identity')
    need(isinstance(ident, dict) and set(ident) == IDENTITY_FIELDS, 'invalid-task',
         'internal identity has missing or unknown fields')
    check_selector({k: ident[k] for k in SELECTOR_FIELDS})
    need(type(ident['identity_schema']) is int and ident['identity_schema'] == 1
         and ident['source_digest_method'] == DIGEST_METHOD
         and is_hash(ident['source_revision']) and ident['source_revision'] == task['source_revision']
         and ident['source_path'] == task['source_path'] and is_hash(ident['object_sha256']),
         'internal-identity-mismatch', 'internal identity is not bound to this source and object')
    need(ident['map_key'] == local_key(task['source_revision'], task['source_path'], task['symbol'],
                                    {k: ident[k] for k in SELECTOR_FIELDS}),
         'internal-identity-mismatch', 'internal symbol map key differs from its TU identity')


def find_internal_function(obj, task):
    ident = task['internal_identity']
    value = {k: ident[k] for k in SELECTOR_FIELDS}
    hits = [s for s in obj.symbols.values() if s.section > 0 and s.name == task['symbol']
            and selector(obj, s) == value]
    need(hits, 'function-symbol-missing', 'object does not define the pinned internal identity')
    need(len(hits) == 1, 'function-symbol-ambiguous', 'internal identity resolves more than once')
    sym = hits[0]
    sec = obj.section(sym.section)
    need(sec.flags & SCN_CNT_CODE and sec.flags & SCN_MEM_EXECUTE and sec.data is not None,
         'candidate-boundary-unsupported', 'internal function needs a complete initialized executable section')
    others = [s for s in obj.symbols.values() if s.section == sym.section and s is not sym
              and (s.is_function or s.storage == STORAGE_EXTERNAL
                   or s.storage == STORAGE_STATIC and s.name != sec.name)]
    need(not others, 'candidate-boundary-unsupported', 'internal section holds another function or alias')
    return sym, sec


class InternalFunction(Function):
    def scoped_symbol(self, sym):
        key = symbol_key(self.obj, sym, self.task)
        return Symbol(sym.index, key, sym.value, sym.section, sym.kind, sym.storage)

    def resolve(self, sym):
        return super().resolve(sym if sym.name == TLS_INDEX or sym.section in self.bound
                               else self.scoped_symbol(sym))

    def secrel_field(self, rel, sym, addend_bytes):
        need(sym.name != TLS_INDEX, 'unsupported-relocation', 'SECREL cannot refer to _tls_index')
        # Check the original section-symbol spelling before replacing its name with a scoped key.
        if sym.section > 0:
            need(sym.name != self.obj.section(sym.section).name, 'unsupported-relocation',
                 'SECREL refers to a section symbol')
        return super().secrel_field(rel, self.scoped_symbol(sym), addend_bytes)

    def ref_field(self, index, offset, rva, what, expect, reason='eh-reference-mismatch'):
        rel = self.relocs[index].get(offset)
        sym = self.obj.symbols[rel.symbol] if rel is not None else None
        if (expect == 'code' and what.endswith('.action') and sym is not None
                and sym.name == '__std_terminate' and sym.section == SYM_UNDEFINED):
            need(sym.storage == STORAGE_EXTERNAL and sym.value == 0 and sym.kind in (0, 0x20)
                 and self.candidate_u32(index, offset, what) == 0,
                 'eh-runtime-import', 'termination action must be an undefined function with no addend')
            entry = self.entries.get(sym.name)
            need(entry is not None and entry.get('size') == 6, 'eh-runtime-import',
                 'termination action map must pin its complete six-byte import thunk')
            # Retain the ordinary ADDR32NB field, relocation consumption and exact RVA checks.
            super().ref_field(index, offset, rva, what, 'external', reason)
            address = entry['rva']
            need(not any(a < address + 6 and address < b for a, b in self.code_ranges),
                 'eh-runtime-import', 'termination thunk overlaps compared candidate code')
            section, thunk = self.image.read(address, 6, 'runtime termination import thunk')
            need(section.flags & SCN_MEM_EXECUTE and thunk[:2] == bytes((0xFF, 0x25)),
                 'eh-runtime-import', 'termination action is not a complete indirect import jump')
            slot = address + 6 + struct.unpack_from('<i', thunk, 2)[0]
            need(slot == runtime_import_slot(self.image), 'eh-runtime-import',
                 'termination jump does not address the named runtime IAT slot')
            for begin, end, _unwind in self.image.runtime_functions():
                need(not (begin < address + 6 and address < end), 'eh-runtime-import',
                     'termination thunk overlaps a procedure with unwind metadata')
            known = self.coverage.setdefault('runtime_actions', [])
            item = {'symbol': sym.name, 'rva': address, 'size': 6, 'iat_rva': slot,
                    'module': 'vcruntime140.dll', 'import': '__std_terminate'}
            if item not in known:
                known.append(item)
            return None
        return super().ref_field(index, offset, rva, what, expect, reason)

    def compare_unwind(self, sec):
        count = super().compare_unwind(sec)
        if sec is self.func_sec:
            for begin, _end, xsec, offset in self.pdata_entries(sec):
                header = self.obj.section(xsec).data[offset]
                need(begin == 0 or (header >> 3) & UNW_FLAG_CHAININFO,
                     'candidate-boundary-unsupported', 'internal section absorbs an independent procedure')
            start, end = self.task['rva'], self.task['rva'] + self.task['size']
            need(not any(start < entry < end for entry in self.image.funclet_entries(None)),
                 'candidate-boundary-unsupported', 'internal primary range absorbs a target funclet')
        return count


def internal_code_sha256(obj, sections, task):
    # Every local target identity enters the hash, even if its spelling is unique in this object.
    identities = [[sec.index, rel.offset, symbol_key(obj, obj.symbols[rel.symbol], task)]
                  for sec in sections for rel in sorted(sec.relocs, key=lambda r: r.offset)]
    return sha256(b'internal-code-section-sha256-v1\0' + code_section_sha256(obj, sections).encode()
                  + json.dumps(identities, sort_keys=True).encode())


def compare(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes, symbol_map,
            diagnostics=None, private_root=ROOT / '.local'):
    """Return a sanitized report dict. Never raises for comparison failures; they become `fail`.

    `symbol_map` is the map file's bytes, whose SHA-256 the report records, or an already parsed
    map, for which the report records no hash and so cannot back a match record.
    """
    coverage = {'code_bytes_total': None, 'code_bytes_exact': 0, 'code_bytes_by_reference': 0,
                'relocations_by_type': {}, 'self_rva_fields': 0, 'unwind_entries': 0, 'unwind_chained_entries': 0,
                'unwind_bytes_exact': 0, 'unwind': 'not-checked', 'aliases_declared': [],
                'funclet_sections': 0, 'funclet_bytes_total': 0, 'funclet_bytes_exact': 0,
                'funclet_bytes_by_reference': 0, 'funclet_ranges': [], 'funclet_end_evidence': {},
                'eh': {'handlers': {}, 'structures': {}, 'ref_fields': 0, 'int_fields': 0, 'bytes': 0,
                       'type_names_compared': 0}}
    report = {'report_schema': REPORT_SCHEMA, 'contract_version': CONTRACT_VERSION,
              'comparator': {'version': COMPARATOR_VERSION, 'source_sha256': comparator_source_sha256()},
              'acceptance': 'not-evaluated', 'result': 'fail', 'reason': None, 'detail': None}
    raw = {}
    obj = sec = function = None
    if isinstance(symbol_map, (bytes, bytearray)):
        # Hashed as read, so a match record can show its runs used the map version it pins.
        report['symbol_map_sha256'] = sha256(symbol_map)
    try:
        if isinstance(symbol_map, (bytes, bytearray)):
            try:
                symbol_map = json.loads(symbol_map)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise Reject('invalid-symbol-map', 'symbol map is not JSON') from None
        check_task(task)
        check_internal_identity(task)
        report.update(task_id=task['task_id'],
                      function={'build_id': task['build_id'], 'rva': task['rva'], 'size': task['size'],
                                'symbol': task['symbol'], 'internal_identity': task['internal_identity']},
                      source={'source_revision': task['source_revision'], 'path': task['source_path']},
                      target={'expected_image_sha256': task['target_image_sha256'],
                              'image_sha256': sha256(image_bytes)},
                      candidate={'object_sha256': sha256(object_bytes)})
        recipe = check_provenance(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes)
        report['recipe'] = {'recipe_sha256': task['recipe_sha256'],
                            'compiler_binary_sha256': recipe['compiler']['binary_sha256'],
                            'compiler_version': recipe['compiler']['version'], 'flags': recipe['flags']}
        # Every entry is read, not only the names the function resolves: an added entry can alias or
        # overlap the range or name an EH handler. A match record is carried across map additions
        # only under tools/symbol_map.py carry_forward_problem, which must track these checks.
        entries, folds, tls_entries = load_symbol_map(task, symbol_map)
        placement_task = dict(task, symbol=task['internal_identity']['map_key'])
        coverage['aliases_declared'] = check_placement(placement_task, entries, folds, tls_entries)
        need(sha256(object_bytes) == task['internal_identity']['object_sha256'],
             'internal-identity-mismatch', 'internal identity names another object')
        obj, image = CoffObject(object_bytes), PeImage(image_bytes)
        check_tls(image, entries, tls_entries)
        _, sec = find_internal_function(obj, task)
        need(len(sec.data) == task['size'], 'function-size-mismatch',
             f'candidate function is {len(sec.data)} bytes; task range is {task["size"]} bytes')
        target_sec, target = image.read(task['rva'], task['size'], 'target function range')
        need(target_sec.flags & SCN_MEM_EXECUTE, 'target-not-code', 'target range is not in an executable section')
        coverage['code_bytes_total'] = task['size']
        check_relocation_layout(sec, len(sec.data), 'function')
        function = InternalFunction(obj, sec, task, entries, image, coverage, tls_entries)
        primary_entries = function.compare_unwind(sec)
        function.compare_code(sec, target, 'code_bytes_exact', 'code_bytes_by_reference')
        function.compare_funclets()
        function.check_complete()
        function.check_target_closure()
        coverage['unwind'] = 'covered' if primary_entries else 'none-in-range'
        need(coverage['code_bytes_exact'] + coverage['code_bytes_by_reference'] == task['size'], 'coverage-gap',
             'not every function byte was compared')
        need(coverage['funclet_bytes_exact'] + coverage['funclet_bytes_by_reference'] == coverage['funclet_bytes_total'],
             'coverage-gap', 'not every funclet byte was compared')
        report.update(result='pass', reason='all-checks-passed', detail='all contract v3 checks passed')
    except Reject as exc:
        report.update(reason=exc.reason, detail=exc.detail)
        raw = exc.raw
    if sec is not None:
        # Function section first, then funclets in the order the exception data reached them.
        funclets = [obj.section(i) for i in function.funclet_order] if function is not None else []
        report['candidate']['code_section_sha256'] = internal_code_sha256(obj, [sec] + funclets, task)
        report['candidate']['code_sections'] = 1 + len(funclets)
    report['coverage'] = coverage
    sanitized(report)
    if diagnostics is not None:
        write_diagnostics(diagnostics, private_root, report, raw)
    return report



def load_json(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, type=Path, help='Task JSON pinning function, source and recipe')
    parser.add_argument('--manifest', default=ROOT / 'builds/target.json', type=Path)
    parser.add_argument('--recipe', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    parser.add_argument('--object', required=True, type=Path, help='Candidate COFF object')
    parser.add_argument('--image', required=True, type=Path, help='Pinned target PE32+ image')
    parser.add_argument('--symbols', required=True, type=Path, help='Symbol-to-RVA map for the target build')
    parser.add_argument('--report', type=Path, help='Write the sanitized report here instead of stdout')
    parser.add_argument('--diagnostics', type=Path, help='Private diagnostics path; must be under .local/')
    args = parser.parse_args()
    try:
        report = compare(load_json(args.task), load_json(args.manifest), args.recipe.read_bytes(),
                         load_json(args.build_record), args.object.read_bytes(), args.image.read_bytes(),
                         args.symbols.read_bytes(), diagnostics=args.diagnostics)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f'FAIL: cannot read inputs: {exc}', file=sys.stderr)
        return 2
    except Reject as exc:
        print(f'FAIL: {exc.reason}: {exc.detail}', file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(text)
    else:
        sys.stdout.write(text)
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
