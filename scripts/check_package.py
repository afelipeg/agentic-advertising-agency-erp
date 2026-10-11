#!/usr/bin/env python3
"""Structural checks without PyYAML; descriptions use JSON-compatible YAML strings."""
import json
from pathlib import Path
import re
import sys
from sync_resources import ROOT, MIRRORS

def check():
    errors=[]
    names={p.name for p in (ROOT/'skills').iterdir() if p.is_dir()}
    workflows=json.loads((ROOT/'contracts/workflows.json').read_text())
    if {v['name'] for v in workflows} != names: errors.append('Workflow catalogue differs from installed skills')
    for skill in sorted((ROOT/'skills').iterdir()):
        text=(skill/'SKILL.md').read_text()
        match=re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: (".*")\n---\n',text)
        if not match or match[1]!=skill.name: errors.append(f'{skill.name}: invalid frontmatter')
        else:
            try:
                description=json.loads(match[2])
                if len(description)<40: errors.append(f'{skill.name}: insufficient description')
            except ValueError: errors.append(f'{skill.name}: invalid description string')
        if len(text.splitlines())>500 or '[TODO' in text: errors.append(f'{skill.name}: unfinished or oversized instructions')
        for source,target in MIRRORS.items():
            expected=(ROOT/source).read_bytes()
            if target=='references/wiring-guide.md': expected=expected.replace(b'../integrations/registry.json',b'provider-registry.json')
            if target=='references/file-mode.md': expected=expected.replace(b'integrations/templates/',b'assets/')
            if not (skill/target).exists() or (skill/target).read_bytes()!=expected: errors.append(f'{skill.name}: resource drift {target}')
        for doc in skill.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
                if link.startswith(('http://','https://','#','mailto:')): continue
                path=(doc.parent/link.split('#')[0]).resolve()
                if not path.is_relative_to(skill.resolve()) or not path.exists(): errors.append(f'{skill.name}: nonportable link {link}')
        if not (skill/'agents/openai.yaml').is_file(): errors.append(f'{skill.name}: missing host UI metadata')
    cases=json.loads((ROOT/'evals/scenarios.json').read_text())['scenarios']
    if len({s['id'] for s in cases})!=len(cases): errors.append('Duplicate scenario IDs')
    if any(s['skill'] not in names for s in cases): errors.append('Behavior scenario names an unavailable skill')
    for path in ROOT.rglob('*.json'):
        if '.git' not in path.parts: json.loads(path.read_text())
    for required in ('README.md','README.es.md','LICENSE','docs/workflow.md','docs/architecture.md','tools/mcp_server.py','scripts/demo.py'):
        if not (ROOT/required).is_file(): errors.append('Missing '+required)
    if errors: print('\n'.join(errors),file=sys.stderr);return 1
    print(f'Package checks passed: {len(names)} skills, {len(cases)} synthetic behavior cases, self-contained resources.')
    return 0

if __name__=='__main__':sys.exit(check())
