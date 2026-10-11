#!/usr/bin/env python3
"""Create an explicitly requested, self-contained Claude skill upload bundle."""
import pathlib
import sys
import zipfile

source, output = map(pathlib.Path, sys.argv[1:])
if not (source / 'SKILL.md').is_file():
    sys.exit('Not a skill directory')
files = sorted(p for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
if any(p.is_symlink() for p in source.rglob('*')):
    sys.exit('Symlink resources are not supported')
try:
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(source.parent))
    print(f'Created {output}; upload through Claude Customize > Skills, then enable it. Connect apps separately.')
except FileExistsError:
    sys.exit('Output already exists; not overwritten')
