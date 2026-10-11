#!/usr/bin/env python3
"""Versioned deterministic business fixtures, not LLM behavioral success rates."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from agency_tools import run

fixtures=json.loads((ROOT/'evals/deterministic.json').read_text())
failed=[]
for fixture in fixtures:
    try:
        actual=run(fixture['tool'],fixture['input'])
        for key,value in fixture['expected'].items():
            if actual.get(key)!=value: raise ValueError('Expected field differs: '+key)
    except Exception as exc:failed.append({'id':fixture['id'],'failure':str(exc)})
print(json.dumps({'suite':'deterministic-business-fixtures','total':len(fixtures),'passed':len(fixtures)-len(failed),'failed':failed,'model_runs':0},indent=2))
sys.exit(1 if failed else 0)
