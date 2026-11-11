"""Read-only local PE fingerprint. Does not execute, modify, unpack or upload inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def fingerprint(path):
    with path.open('rb') as source:
        header = source.read(64)
        if len(header) != 64 or header[:2] != b'MZ':
            raise ValueError('Input is not a PE executable')
        source.seek(struct.unpack_from('<I', header, 60)[0])
        pe = source.read(6)
        if len(pe) != 6 or pe[:4] != b'PE\0\0':
            raise ValueError('Invalid PE signature')
        if struct.unpack_from('<H', pe, 4)[0] != 0x8664:
            raise ValueError('Expected x86-64 PE for Skyrim SE')
        source.seek(0)
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--store', required=True)
    parser.add_argument('--version', required=True, help='Actual version, asserted by researcher')
    args = parser.parse_args()
    try:
        digest = fingerprint(args.image)
    except (OSError, ValueError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'schema_version': 1, 'status': 'pinned', 'build_id': None,
                      'game': 'The Elder Scrolls V: Skyrim Special Edition', 'store': args.store,
                      'version': args.version, 'architecture': 'x86-64', 'image_sha256': digest,
                      'scope_notes': 'Candidate: review identity and assign build_id before publication.'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
