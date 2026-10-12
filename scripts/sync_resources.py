#!/usr/bin/env python3
"""Copy canonical shared resources into independently installable skill folders.

Shared files go to every skill. ERP domain references go only to the skills whose
contracts/workflows.json entry lists them, so each skill stays self-contained but small.
"""
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from agency_tools import SCHEMAS, OUTPUT_SCHEMAS

MIRRORS={
    'docs/control-contract.md':'references/control-contract.md',
    'docs/agency-policy.md':'references/agency-policy.md',
    'docs/operations-playbook.md':'references/operations-playbook.md',
    'docs/offline-media.md':'references/offline-media.md',
    'docs/file-mode.md':'references/file-mode.md',
    'docs/integrations.md':'references/wiring-guide.md',
    'docs/erp-reference/e2e-circuit.md':'references/erp/e2e-circuit.md',
    'integrations/registry.json':'references/provider-registry.json',
    'contracts/tool-inputs.json':'references/tool-contracts.json',
    'contracts/tool-outputs.json':'references/tool-outputs.json',
    'contracts/handoff-schema.json':'references/handoff-schema.json',
    'tools/agency_tools.py':'scripts/agency_tools.py',
    'tools/agency_policy.py':'scripts/agency_policy.py',
    'scripts/normalize_files.py':'scripts/normalize_files.py',
}
ERP_DIR=ROOT/'docs/erp-reference'

def mirrored_bytes(source,target):
    data=(ROOT/source).read_bytes()
    if target=='references/wiring-guide.md':
        data=data.replace(b'../integrations/registry.json',b'provider-registry.json')
    if target=='references/file-mode.md':
        data=data.replace(b'integrations/templates/',b'assets/')
    if target=='references/operations-playbook.md':
        data=data.replace(b'](erp-reference/README.md)',b'](erp/e2e-circuit.md)')
    return data

def erp_references():
    """Map skill name -> list of ERP reference stems from the workflow catalogue."""
    catalogue=json.loads((ROOT/'contracts/workflows.json').read_text())
    result={}
    for entry in catalogue:
        refs=entry.get('references',[])
        for ref in refs:
            if not (ERP_DIR/f'{ref}.md').is_file():
                raise SystemExit(f"{entry['name']}: unknown ERP reference {ref}")
        result[entry['name']]=refs
    return result

POLICY_PREFIX='Agency policy: '
ANCHOR=re.compile(r'^Read \[control-contract\.md\]\(references/control-contract\.md\) first.*$',re.M)

def policy_line(entry):
    """The one SKILL.md line that connects a skill to its AGENCY.md sections; generated from the catalogue."""
    sections=', '.join(f'`{s}`' for s in entry['policy'])
    route=' Route approvers with `approval_route`.' if 'approvals' in entry['policy'] else ''
    return (f"{POLICY_PREFIX}apply {sections} from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`."
            f"{route} Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.")

def render_skill(text,entry):
    """Insert or refresh the policy line right after the control-contract line."""
    lines=[l for l in text.split('\n') if not l.startswith(POLICY_PREFIX)]
    text='\n'.join(lines)
    text=re.sub(r'\n\n\n+','\n\n',text)
    match=ANCHOR.search(text)
    if not match:
        raise SystemExit(f"{entry['name']}: SKILL.md lacks the control-contract line")
    return text[:match.end()]+'\n\n'+policy_line(entry)+text[match.end():]

def render_workflow_doc():
    """Render docs/workflow.md from the catalogue so routing docs never drift."""
    catalogue=json.loads((ROOT/'contracts/workflows.json').read_text())
    out=['# Workflow catalogue','',
         'Generated from `contracts/workflows.json` by `scripts/sync_resources.py`; edit the catalogue, not this file.','',
         'Start with agency-orchestrator and agency-integrations; run only relevant stages. The circuit map is [erp-reference/e2e-circuit.md](erp-reference/e2e-circuit.md); detailed rules live in [operations-playbook.md](operations-playbook.md) and the [ERP functional reference](erp-reference/README.md). Skills accept connected tools or supplied files ([file-mode.md](file-mode.md), [integrations.md](integrations.md)) and apply the agency parameters from `AGENCY.md` ([agency-policy.md](agency-policy.md)). This catalogue is a routing index, not authorization.','']
    for w in catalogue:
        refs=', '.join(f'[{r}](erp-reference/{r}.md)' for r in w['references']) or 'circuit map only'
        tools=', '.join(f'`{t}`' for t in w['tools']) or 'none'
        out+=[f"## {w['name']}",'',w['description'],'',f"**Inputs:** {w['inputs']}",'',
              '**Outputs:** '+', '.join(f'`{o}`' for o in w['outputs']),'',
              f"**ERP reference:** {refs}. **Agency policy:** "+(', '.join(f'`{p}`' for p in w['policy']) or 'none')+f". **Tools:** {tools}.",'',
              f"**Owner:** {w['owner']}. **Next:** {w['next_stage']}.",'']
        out+=[f'{i}. {step}' for i,step in enumerate(w['procedure'],1)]+['']
    return '\n'.join(out)

def tool_contracts():
    return {'contracts/tool-inputs.json':json.dumps(SCHEMAS,indent=2)+'\n','contracts/tool-outputs.json':json.dumps(OUTPUT_SCHEMAS,indent=2)+'\n'}

def sync():
    for path,text in tool_contracts().items():
        (ROOT/path).write_text(text)
    refs=erp_references()
    (ROOT/'docs/workflow.md').write_text(render_workflow_doc())
    catalogue={w['name']:w for w in json.loads((ROOT/'contracts/workflows.json').read_text())}
    for skill in sorted((ROOT/'skills').iterdir()):
        if not skill.is_dir():
            continue
        for source,target in MIRRORS.items():
            (skill/target).parent.mkdir(parents=True,exist_ok=True)
            (skill/target).write_bytes(mirrored_bytes(source,target))
        if skill.name in catalogue:
            md=skill/'SKILL.md'
            md.write_text(render_skill(md.read_text(),catalogue[skill.name]))
        erp=skill/'references'/'erp'
        wanted={f'{r}.md' for r in refs.get(skill.name,[])}|{'e2e-circuit.md'}
        for stale in erp.glob('*.md'):
            if stale.name not in wanted:
                stale.unlink()
        for name in sorted(wanted-{'e2e-circuit.md'}):
            shutil.copyfile(ERP_DIR/name,erp/name)
        templates={t.name:t for t in (ROOT/'integrations/templates').glob('*.csv')}
        (skill/'assets').mkdir(exist_ok=True)
        for stale in (skill/'assets').glob('*.csv'):
            if stale.name not in templates:
                stale.unlink()
        for name,template in templates.items():
            shutil.copyfile(template,skill/'assets'/name)
    print('Synced shared resources and per-skill ERP references into all self-contained skills.')

if __name__=='__main__':
    sync()
