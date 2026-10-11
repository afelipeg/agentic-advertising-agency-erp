import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,readFile,access,symlink,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const cli=join(root,'bin/agency-erp.mjs');
function run(args,cwd){return spawnSync(process.execPath,[cli,...args],{cwd,encoding:'utf8',shell:false});}

test('selected install is self-contained and never overwrites',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'agency-install-'));
  try{
    let r=run(['install','--agent','codex','--skill','agency-plan-changes','--dry-run'],dir);assert.equal(r.status,0,r.stderr);
    await assert.rejects(access(join(dir,'.agents')));
    r=run(['install','--agent','codex','--skill','agency-plan-changes'],dir);assert.equal(r.status,0,r.stderr);
    const skill=join(dir,'.agents/skills/agency-plan-changes');
    const md=await readFile(join(skill,'SKILL.md'),'utf8');assert.match(md,/agency-plan-changes/);
    for(const f of ['references/control-contract.md','references/operations-playbook.md','references/wiring-guide.md','scripts/normalize_files.py','scripts/agency_tools.py','assets/plan.csv']) await access(join(skill,f));
    const tool=spawnSync('python3',[join(skill,'scripts/agency_tools.py'),'flat_rebate'],{input:JSON.stringify({currency:'USD',eligible_minor:100,rate_bps:500,client_share_bps:0}),encoding:'utf8'});assert.equal(tool.status,0,tool.stderr);assert.equal(JSON.parse(tool.stdout).rebate_minor,5);
    r=run(['install','--agent','codex','--skill','agency-plan-changes'],dir);assert.equal(r.status,1);assert.match(r.stderr,/Already exists/);
  }finally{await rm(dir,{recursive:true,force:true});}
});
test('invalid names and symlink destinations are rejected',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'agency-symlink-')),outside=await mkdtemp(join(tmpdir(),'agency-outside-'));
  try{
    assert.equal(run(['install','--agent','codex','--skill','../../evil'],dir).status,1);
    await symlink(outside,join(dir,'.agents'));
    const r=run(['install','--agent','codex','--skill','agency-production'],dir);assert.equal(r.status,1);assert.match(r.stderr,/Symlink/);assert.deepEqual(await readdir(outside),[]);
  }finally{await rm(dir,{recursive:true,force:true});await rm(outside,{recursive:true,force:true});}
});
test('web export warns about instruction adaptation and is exclusive',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'agency-export-'));
  try{
    const out=join(dir,'reference.md');let r=run(['export','--host','gpt','--out',out],dir);assert.equal(r.status,0,r.stderr);
    const text=await readFile(out,'utf8');assert.match(text,/not an executable installation/);assert.match(text,/Agency ERP end-to-end circuit/);assert.match(text,/Plan Changes/);assert.match(text,/mx-cfdi-pac/);assert.match(text,/supermetrics/);
    r=run(['export','--host','gpt','--out',out],dir);assert.equal(r.status,1);
  }finally{await rm(dir,{recursive:true,force:true});}
});
test('bundle includes one portable skill and no gold evaluations',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'agency-bundle-'));
  try{
    const out=join(dir,'production.zip'),r=run(['bundle','--skill','agency-production','--out',out],dir);assert.equal(r.status,0,r.stderr);
    const inspect=spawnSync('python3',['-c','import sys,zipfile,json; print(json.dumps(zipfile.ZipFile(sys.argv[1]).namelist()))',out],{encoding:'utf8'});
    assert.equal(inspect.status,0);const files=JSON.parse(inspect.stdout);assert(files.includes('agency-production/SKILL.md'));assert(files.includes('agency-production/references/file-mode.md'));assert(files.every(f=>!f.includes('evals')));
  }finally{await rm(dir,{recursive:true,force:true});}
});
test('gemini target installs into .gemini/skills',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'agency-gemini-'));
  try{
    const r=run(['install','--agent','gemini','--skill','agency-collections'],dir);assert.equal(r.status,0,r.stderr);
    await access(join(dir,'.gemini/skills/agency-collections/SKILL.md'));
  }finally{await rm(dir,{recursive:true,force:true});}
});
