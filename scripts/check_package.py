#!/usr/bin/env python3
"""Structural checks without PyYAML; descriptions use JSON-compatible YAML strings."""
import json
from pathlib import Path
import re
import sys
from sync_resources import ROOT, MIRRORS, ERP_DIR, mirrored_bytes, erp_references, render_workflow_doc, tool_contracts
sys.path.insert(0,str(ROOT/'tools'))
from agency_tools import SCHEMAS

WORKFLOW_KEYS={'name','title','description','inputs','outputs','owner','next_stage','procedure','references','tools'}

def check():
    errors=[]
    names={p.name for p in (ROOT/'skills').iterdir() if p.is_dir()}
    workflows=json.loads((ROOT/'contracts/workflows.json').read_text())
    by_name={w['name']:w for w in workflows}
    if set(by_name) != names or len(by_name)!=len(workflows): errors.append('Workflow catalogue differs from installed skills')
    try:
        refs=erp_references()
    except SystemExit as exc:
        errors.append(str(exc)); refs={}
    if (ROOT/'docs/workflow.md').read_text()!=render_workflow_doc(): errors.append('docs/workflow.md is stale; run npm run sync')
    for path,text in tool_contracts().items():
        if (ROOT/path).read_text()!=text: errors.append(f'{path} is stale; run npm run sync')
    templates={p.name:p.read_bytes() for p in (ROOT/'integrations/templates').glob('*.csv')}
    for w in workflows:
        if set(w)!=WORKFLOW_KEYS: errors.append(f"{w.get('name')}: workflow keys differ")
        if not isinstance(w.get('inputs'),str) or not isinstance(w.get('next_stage'),str): errors.append(f"{w.get('name')}: inputs/next_stage must be strings")
        for tool in w.get('tools',[]):
            if tool not in SCHEMAS: errors.append(f"{w['name']}: unknown tool {tool}")
    for skill in sorted((ROOT/'skills').iterdir()):
        if not skill.is_dir(): continue
        text=(skill/'SKILL.md').read_text()
        match=re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: (".*")\n---\n',text)
        if not match or match[1]!=skill.name: errors.append(f'{skill.name}: invalid frontmatter')
        else:
            try:
                description=json.loads(match[2])
                if not 40<=len(description)<=200: errors.append(f'{skill.name}: description length outside 40..200 (Claude app upload limit)')
                if skill.name in by_name and by_name[skill.name]['description']!=description: errors.append(f'{skill.name}: description differs from workflow catalogue')
            except ValueError: errors.append(f'{skill.name}: invalid description string')
        if len(text.splitlines())>500 or '[TODO' in text: errors.append(f'{skill.name}: unfinished or oversized instructions')
        for tool in by_name.get(skill.name,{}).get('tools',[]):
            if tool not in text: errors.append(f'{skill.name}: catalogue tool {tool} not explained in SKILL.md')
        for source,target in MIRRORS.items():
            if not (skill/target).exists() or (skill/target).read_bytes()!=mirrored_bytes(source,target): errors.append(f'{skill.name}: resource drift {target}')
        wanted={f'{r}.md' for r in refs.get(skill.name,[])}|{'e2e-circuit.md'}
        present={p.name for p in (skill/'references'/'erp').glob('*.md')}
        if present!=wanted: errors.append(f'{skill.name}: ERP references differ from catalogue')
        for name in wanted-{'e2e-circuit.md'}:
            if (skill/'references'/'erp'/name).exists() and (skill/'references'/'erp'/name).read_bytes()!=(ERP_DIR/name).read_bytes(): errors.append(f'{skill.name}: ERP reference drift {name}')
        for doc in skill.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
                if link.startswith(('http://','https://','#','mailto:')): continue
                path=(doc.parent/link.split('#')[0]).resolve()
                if not path.is_relative_to(skill.resolve()) or not path.exists(): errors.append(f'{skill.name}: nonportable link {link} in {doc.relative_to(skill)}')
        assets={p.name:p.read_bytes() for p in (skill/'assets').glob('*.csv')}
        if assets!=templates: errors.append(f'{skill.name}: asset templates drift')
        if not (skill/'agents/openai.yaml').is_file(): errors.append(f'{skill.name}: missing host UI metadata')
    cases=json.loads((ROOT/'evals/scenarios.json').read_text())['scenarios']
    if len({s['id'] for s in cases})!=len(cases): errors.append('Duplicate scenario IDs')
    if any(s['skill'] not in names for s in cases): errors.append('Behavior scenario names an unavailable skill')
    uncovered=sorted(names-{s['skill'] for s in cases})
    if uncovered: errors.append('Skills without behavior scenarios: '+', '.join(uncovered))
    for path in ROOT.rglob('*.json'):
        if '.git' not in path.parts and 'node_modules' not in path.parts: json.loads(path.read_text())
    for required in ('README.md','README.es.md','LICENSE','AGENTS.md','docs/workflow.md','docs/architecture.md','docs/erp-reference/e2e-circuit.md','tools/mcp_server.py','scripts/demo.py','.claude-plugin/marketplace.json','.claude-plugin/plugin.json','gemini-extension.json','GEMINI.md','scripts/build_release.py'):
        if not (ROOT/required).is_file(): errors.append('Missing '+required)
    versions={json.loads((ROOT/f).read_text())['version'] for f in ('package.json','.claude-plugin/plugin.json','gemini-extension.json')}
    if len(versions)!=1: errors.append('package.json, plugin.json and gemini-extension.json versions differ')
    if errors: print('\n'.join(errors),file=sys.stderr);return 1
    print(f'Package checks passed: {len(names)} skills, {len(SCHEMAS)} local tools, {len(cases)} synthetic behavior cases, self-contained resources.')
    return 0

if __name__=='__main__':sys.exit(check())
