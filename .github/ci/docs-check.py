"""Validate tracked documentation as inert source; never evaluate MDX or fetch URLs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit
from typing import TypedDict

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


class DocumentRecord(TypedDict):
    path: str
    bytes: int
    sha256: str


class SourceManifest(TypedDict):
    format_version: int
    kind: str
    documents: list[DocumentRecord]


def document(root: Path, name: str) -> tuple[Path, bytes, str]:
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise ValueError('unsafe-document-path')
    path = root / name
    if any(part.is_symlink() for part in [path, *path.parents] if part != root.parent):
        raise ValueError('symlink-document-path')
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('missing-document')
    if not 0 < path.stat().st_size <= MAX_DOCUMENT_BYTES:
        raise ValueError('invalid-document-size')
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    if '\0' in text:
        raise ValueError('invalid-document-content')
    return path, raw, text


def validate(root: Path, names: list[str]) -> SourceManifest:
    names = sorted(name for name in names if name.endswith(('.md', '.mdx')))
    if not names or len(names) != len(set(names)):
        raise ValueError('invalid-document-inventory')
    records: list[DocumentRecord] = []
    for name in names:
        path, raw, text = document(root, name)
        for target in re.findall(r'\]\(([^\s)]+)\)', text):
            url = urlsplit(target.strip('<>'))
            if url.scheme:
                if url.scheme not in ('https', 'http', 'mailto'):
                    raise ValueError('unsupported-link-scheme')
                continue
            if url.netloc:
                raise ValueError('ambiguous-link-target')
            if not url.path:  # Fragment-only links do not leave the document.
                continue
            local = unquote(url.path)
            if '\\' in local or '\0' in local:
                raise ValueError('unsafe-local-link')
            candidate = path.parent / local
            if not candidate.resolve().is_relative_to(root.resolve()):
                raise ValueError('local-link-outside-repository')
            if candidate.is_symlink() or not candidate.exists():
                raise ValueError('missing-or-symlink-link-target')
        records.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    return {'format_version': 1, 'kind': 'inert-documentation-source', 'documents': records}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', action='store_true')
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        output = subprocess.check_output(['git', 'ls-files', '-z', '--', '*.md', '*.mdx'])
        names = [name for name in output.decode('utf-8').split('\0') if name]
        record = validate(root, names)
        if args.manifest:
            print(json.dumps(record, sort_keys=True, indent=2))
        else:
            print('PASS:', len(record['documents']), 'tracked documentation files')
        return 0
    except (ValueError, OSError, subprocess.SubprocessError):
        print('FAIL: invalid tracked documentation or local link')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
