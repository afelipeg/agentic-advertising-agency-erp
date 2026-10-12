#!/usr/bin/env node
import { readdir, readFile, lstat, mkdir, cp, access } from 'node:fs/promises';
import { constants } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import { spawnSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const names = (await readdir(join(root, 'skills'))).sort();
const help = `agency-erp list
agency-erp install --agent codex|claude-code|gemini [--skill NAME] [--global] [--cwd PATH] [--dry-run]
agency-erp policy init [--global] [--cwd PATH] [--dry-run]
agency-erp policy check [--file PATH]
agency-erp doctor
agency-erp export --host claude-ai|gpt --out PATH
agency-erp bundle --skill NAME --out PATH.zip
agency-erp connect-plan --profile solo|studio|performance|agency
agency-erp import --kind KIND --file PATH --out PATH.json --tenant ID --client ID --job ID [--sheet NAME]
agency-erp tool NAME < input.json
agency-erp mcp
agency-erp demo

Install adds self-contained skills only; it never connects accounts or overwrites existing skills.
Policy init writes an example AGENCY.md (your agency's parameters) to the project or ~/.agency-erp; it never overwrites one.
Export creates an instruction document for a web assistant, not a native skill installation.`;

async function exists(path) { try { await access(path); return true; } catch { return false; } }
async function rejectSymlinks(path) {
  let current = resolve(path);
  while (true) {
    try { if ((await lstat(current)).isSymbolicLink()) throw new Error(`Symlink destination is not allowed: ${current}`); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
}
function options(values) {
  const o = {};
  for (let i=0;i<values.length;i++) {
    const key = values[i];
    if (!['--agent','--skill','--cwd','--global','--dry-run','--host','--out','--profile','--file'].includes(key) || key in o) throw new Error(`Unknown or repeated option: ${key}`);
    if (['--global','--dry-run'].includes(key)) o[key] = true;
    else { if (!values[i+1] || values[i+1].startsWith('--')) throw new Error(`Missing value: ${key}`); o[key]=values[++i]; }
  }
  return o;
}
function python(script, tool) {
  const result = spawnSync('python3', [join(root, 'tools', script), ...(tool ? [tool] : [])], {stdio:'inherit', shell:false});
  if (result.error) throw new Error('Python 3 is required for local tools and MCP. Skill instructions can be used without it.');
  process.exitCode = result.status ?? 1;
}
try {
  const [command, ...rest] = args;
  if (!command || command === '--help' || command === 'help') console.log(help);
  else if (command === 'list') console.log(names.join('\n'));
  else if (command === 'install') {
    const o=options(rest), agent=o['--agent'];
    if (!['codex','claude-code','gemini'].includes(agent)) throw new Error('Select --agent codex, claude-code or gemini. See export for web assistants.');
    const selected=o['--skill'] ? [o['--skill']] : names;
    if (selected.some(n=>!names.includes(n))) throw new Error('Unknown skill. Run list.');
    const base=o['--global'] ? homedir() : resolve(o['--cwd'] || process.cwd());
    const dest=join(base, {codex:'.agents','claude-code':'.claude',gemini:'.gemini'}[agent], 'skills');
    await rejectSymlinks(dest);
    // Preflight all conflicts before creating anything. Never recursively remove user files.
    for (const name of selected) if (await exists(join(dest,name))) throw new Error(`Already exists: ${join(dest,name)}. Remove or archive it yourself before updating.`);
    for (const name of selected) {
      const target=join(dest,name);
      if (!o['--dry-run']) { await mkdir(dest,{recursive:true}); await cp(join(root,'skills',name),target,{recursive:true,errorOnExist:true,force:false}); }
      console.log(`${o['--dry-run'] ? 'Would install' : 'Installed'} ${name} → ${target}`);
    }
  } else if (command === 'policy') {
    const [sub, ...more]=rest, o=options(more);
    const allowed={init:['--global','--cwd','--dry-run'],check:['--file']}[sub];
    if (allowed && Object.keys(o).some(k=>!allowed.includes(k))) throw new Error(sub==='init' ? 'Use policy init [--global] [--cwd PATH] [--dry-run]' : 'Use policy check [--file PATH]');
    if (sub === 'init') {
      if (o['--global'] && o['--cwd']) throw new Error('Choose --global or --cwd, not both.');
      const dir=o['--global'] ? join(homedir(),'.agency-erp') : resolve(o['--cwd'] || process.cwd());
      const target=join(dir,'AGENCY.md');
      await rejectSymlinks(target);
      if (await exists(target)) throw new Error(`Already exists: ${target}. Edit it, or move it aside yourself before creating a new one.`);
      if (!o['--dry-run']) {
        await mkdir(dir,{recursive:true});
        const {open}=await import('node:fs/promises');
        const file=await open(target,'wx'); try { await file.writeFile(await readFile(join(root,'AGENCY.md'))); } finally { await file.close(); }
      }
      console.log(`${o['--dry-run'] ? 'Would write' : 'Wrote'} example policy → ${target}`);
      console.log('Replace the example values, then run: agency-erp policy check' + (o['--global'] ? ` --file ${target}` : ''));
      if (o['--global']) console.log(`Point each project at it with one line in AGENTS.md or CLAUDE.md: "Read ${target} before using any agency-erp skill."`);
    } else if (sub === 'check') {
      const result=spawnSync('python3',[join(root,'tools','agency_policy.py'),...(o['--file'] ? [resolve(o['--file'])] : [])],{stdio:'inherit',shell:false});
      if (result.error) throw new Error('Python 3 is required to validate AGENCY.md.');
      process.exitCode=result.status ?? 1;
    } else throw new Error('Use policy init or policy check');
  } else if (command === 'doctor') {
    const py=spawnSync('python3',['--version'],{encoding:'utf8',shell:false});
    console.log(JSON.stringify({node:process.version,python:py.status===0?(py.stdout||py.stderr).trim():null,skills:names.length,accounts_connected_by_package:false,production_runtime_included:false},null,2));
  } else if (command === 'export') {
    const o=options(rest);
    if (!['claude-ai','gpt'].includes(o['--host']) || !o['--out']) throw new Error('Use --host claude-ai|gpt --out PATH');
    const out=resolve(o['--out']);
    await rejectSymlinks(out);
    const {open}=await import('node:fs/promises');
    const sections=[await readFile(join(root,'docs','web-assistant.md'),'utf8'),await readFile(join(root,'docs','control-contract.md'),'utf8'),await readFile(join(root,'docs','erp-reference','e2e-circuit.md'),'utf8')];
    for (const name of names) sections.push((await readFile(join(root,'skills',name,'SKILL.md'),'utf8')).replace(/^---\n[\s\S]*?\n---\n/,''));
    sections.push('# Provider registry\n```json\n'+await readFile(join(root,'integrations','registry.json'),'utf8')+'\n```');
    const file=await open(out,'wx'); try { await file.writeFile(sections.join('\n\n---\n\n')); } finally { await file.close(); }
    console.log(`Exported instruction reference to ${out}. Follow the web-assistant guide to configure connectors; this is not an automatic skill install.`);
  } else if(command==='bundle') {
    const o=options(rest);
    if(!names.includes(o['--skill']) || !o['--out']?.endsWith('.zip')) throw new Error('Use bundle --skill NAME --out PATH.zip');
    const out=resolve(o['--out']); await rejectSymlinks(out);
    const result=spawnSync('python3',[join(root,'scripts','bundle.py'),join(root,'skills',o['--skill']),out],{stdio:'inherit',shell:false});
    if(result.error) throw new Error('Python 3 is required for skill upload bundles.');
    process.exitCode=result.status??1;
  } else if(command==='connect-plan') {
    const o=options(rest), profiles=JSON.parse(await readFile(join(root,'integrations','profiles.json'),'utf8'));
    if(!Object.hasOwn(profiles,o['--profile'])) throw new Error('Select --profile solo|studio|performance|agency');
    console.log(JSON.stringify(profiles[o['--profile']],null,2));
  } else if(command==='import') {
    const result=spawnSync('python3',[join(root,'scripts','normalize_files.py'),...rest],{stdio:'inherit',shell:false});
    if(result.error) throw new Error('Python 3 is required for file normalization.');
    process.exitCode=result.status??1;
  } else if (command==='tool') {
    if(rest.length!==1) throw new Error('Use tool NAME < input.json');
    python('agency_tools.py',rest[0]);
  } else if (command==='mcp') python('mcp_server.py');
  else if (command==='demo') {
    const result=spawnSync('python3',[join(root,'scripts','demo.py')],{stdio:'inherit',shell:false});
    if(result.error) throw new Error('Python 3 is required for the offline demo.');
    process.exitCode=result.status??1;
  } else throw new Error(`Unknown command: ${command}`);
} catch(e) { console.error(e.message); process.exitCode=1; }
