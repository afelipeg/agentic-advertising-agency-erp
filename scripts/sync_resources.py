#!/usr/bin/env python3
"""Copy canonical shared resources into independently installable skill folders."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from agency_tools import SCHEMAS, OUTPUT_SCHEMAS

MIRRORS={
    'docs/control-contract.md':'references/control-contract.md',
    'docs/operations-playbook.md':'references/operations-playbook.md',
    'docs/offline-media.md':'references/offline-media.md',
    'docs/file-mode.md':'references/file-mode.md',
    'docs/integrations.md':'references/wiring-guide.md',
    'integrations/registry.json':'references/provider-registry.json',
    'contracts/tool-inputs.json':'references/tool-contracts.json',
    'contracts/tool-outputs.json':'references/tool-outputs.json',
    'contracts/handoff-schema.json':'references/handoff-schema.json',
    'tools/agency_tools.py':'scripts/agency_tools.py',
    'scripts/normalize_files.py':'scripts/normalize_files.py',
}
if __name__=='__main__':
    (ROOT/'contracts/tool-inputs.json').write_text(json.dumps(SCHEMAS,indent=2)+'\n')
    (ROOT/'contracts/tool-outputs.json').write_text(json.dumps(OUTPUT_SCHEMAS,indent=2)+'\n')
    for skill in sorted((ROOT/'skills').iterdir()):
        for source,target in MIRRORS.items():
            (skill/target).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/source,skill/target)
            if target == 'references/wiring-guide.md':
                p=skill/target
                p.write_text(p.read_text().replace('../integrations/registry.json','provider-registry.json'))
            if target == 'references/file-mode.md':
                p=skill/target
                p.write_text(p.read_text().replace('integrations/templates/','assets/'))
        for template in (ROOT/'integrations/templates').glob('*.csv'):
            dest=skill/'assets'/template.name;dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(template,dest)
    print('Synced shared resources into all self-contained skills.')
