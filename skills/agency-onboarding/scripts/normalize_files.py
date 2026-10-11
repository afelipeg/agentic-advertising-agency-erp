#!/usr/bin/env python3
"""Validate explicit redacted CSV/XLSX inputs; never sends anything to an LLM."""
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

MAX_BYTES = 20*1024*1024
MAX_ROWS = 10000
ID = 'id'
TEMPLATES = {
    'plan': {'tenant_id':ID,'client_id':ID,'job_id':ID,'line_id':ID,'account_id':ID,'supplier_id':ID,'channel':ID,'currency':'currency','currency_exponent':'exponent','amount_minor':'int','committed_minor':'int','start_date':'date','end_date':'date'},
    'broadcast-order': {'tenant_id':ID,'client_id':ID,'job_id':ID,'spot_id':ID,'order_id':ID,'station_id':ID,'program_id':ID,'material_id':ID,'air_date':'date','air_time':'time','timezone':'zone','duration_seconds':'positive','currency':'currency','currency_exponent':'exponent','amount_minor':'int'},
    'emission': {'tenant_id':ID,'client_id':ID,'job_id':ID,'event_id':ID,'station_id':ID,'program_id':ID,'material_id':ID,'air_date':'date','air_time':'time','timezone':'zone','duration_seconds':'positive','source_ref':ID},
    'ooh': {'tenant_id':ID,'client_id':ID,'job_id':ID,'line_id':ID,'site_id':ID,'supplier_id':ID,'material_id':ID,'start_date':'date','end_date':'date','currency':'currency','currency_exponent':'exponent','amount_minor':'int','evidence_ref':ID},
    'invoice': {'tenant_id':ID,'client_id':ID,'job_id':ID,'document_id':ID,'supplier_id':ID,'order_id':ID,'document_type':'document-type','currency':'currency','currency_exponent':'exponent','net_minor':'int','tax_minor':'int','gross_minor':'int','issue_date':'date','due_date':'date','source_ref':ID},
    'rating': {'tenant_id':ID,'client_id':ID,'job_id':ID,'book_id':ID,'provider_id':ID,'market_id':ID,'target_id':ID,'station_id':ID,'program_id':ID,'period_start':'date','period_end':'date','rating_bps':'optional-int','universe':'positive','source_ref':ID},
}

def convert(value, kind, row_number, field):
    if isinstance(value,(date,datetime)):
        value = value.strftime('%Y-%m-%d' if kind=='date' else '%H:%M:%S')
    text = str(value).strip() if value is not None else ''
    error = f'row {row_number}, field {field}: expected {kind}'
    if kind == 'optional-int' and text == '': return None
    if kind in ('int','positive','exponent','optional-int'):
        if not re.fullmatch('[0-9]+',text): raise ValueError(error)
        result = int(text)
        if result > 9_007_199_254_740_991 or (kind=='positive' and result==0) or (kind=='exponent' and result>6): raise ValueError(error)
        return result
    if kind == 'date':
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',text): raise ValueError(error)
        try: date.fromisoformat(text)
        except ValueError: raise ValueError(error) from None
        return text
    patterns={'id':r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}','currency':r'[A-Z]{3}','time':r'(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]','zone':r'[A-Za-z_]+(?:/[A-Za-z0-9_+.-]+)*','document-type':r'(?:invoice|credit)'}
    if not re.fullmatch(patterns[kind],text): raise ValueError(error)
    if kind=='zone':
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try: ZoneInfo(text)
        except ZoneInfoNotFoundError: raise ValueError(error) from None
    return text

def load_rows(path, sheet=None):
    path=Path(path)
    source_sheet=None
    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
        raise ValueError('Source must be a regular non-symlink file under 20 MiB')
    raw=path.read_bytes()
    if path.suffix.lower()=='.csv':
        if sheet: raise ValueError('--sheet applies only to XLSX')
        rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig')),strict=True))
    elif path.suffix.lower()=='.xlsx':
        # Reject archives that would expand beyond the bounded memory allowance.
        import zipfile
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 100*1024*1024:
                raise ValueError('XLSX expanded content exceeds 100 MiB')
        try: import openpyxl
        except ImportError: raise ValueError('XLSX support requires optional openpyxl; use a values-only UTF-8 CSV instead') from None
        workbook=openpyxl.load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
        try:
            if sheet is None and len(workbook.sheetnames)!=1: raise ValueError('Select --sheet for a multi-sheet XLSX; sheets are never silently merged')
            if sheet and sheet not in workbook.sheetnames: raise ValueError('Requested sheet does not exist')
            ws=workbook[sheet] if sheet else workbook.worksheets[0]
            source_sheet=ws.title
            rows=[]
            for cells in ws.iter_rows():
                if len(rows)>MAX_ROWS: raise ValueError('Too many rows')
                if any(c.data_type=='f' for c in cells): raise ValueError('Formula cells are not accepted; export reviewed calculated values first')
                rows.append([c.value for c in cells])
        finally: workbook.close()
    else: raise ValueError('Use CSV or XLSX; macro workbooks, PDFs and images are not normalized by this command')
    return raw,rows,source_sheet

def normalize(kind, source, tenant, client, job, sheet=None):
    if kind not in TEMPLATES: raise ValueError('Unknown import kind')
    for field,value in [('tenant_id',tenant),('client_id',client),('job_id',job)]: convert(value,'id',0,field)
    raw,rows,source_sheet=load_rows(source,sheet)
    if not rows: raise ValueError('Empty source')
    headers=[str(x).strip() if x is not None else '' for x in rows[0]]
    if len(headers)!=len(set(headers)) or set(headers)!=set(TEMPLATES[kind]):
        raise ValueError('Headers must exactly match the template; rename/map fields explicitly and remove unrelated/PII columns')
    records=[];seen=set();currency_exp={}
    key={'plan':'line_id','broadcast-order':'spot_id','emission':'event_id','ooh':'line_id','invoice':'document_id','rating':None}[kind]
    for i,row in enumerate(rows[1:],2):
        if all(x is None or str(x).strip()=='' for x in row): continue
        if len(row)!=len(headers): raise ValueError(f'row {i}: wrong field count')
        item={field:convert(value,TEMPLATES[kind][field],i,field) for field,value in zip(headers,row)}
        if (item['tenant_id'],item['client_id'],item['job_id'])!=(tenant,client,job): raise ValueError(f'row {i}: scope mismatch')
        identity=item[key] if key else tuple(item[f] for f in ('book_id','market_id','target_id','station_id','program_id','period_start','period_end'))
        if identity in seen: raise ValueError(f'row {i}: duplicate identity')
        seen.add(identity)
        if 'currency' in item:
            cur,ex=item['currency'],item['currency_exponent']
            if cur in currency_exp and currency_exp[cur]!=ex: raise ValueError(f'row {i}: conflicting currency exponent')
            currency_exp[cur]=ex
        for start,end in [('start_date','end_date'),('period_start','period_end')]:
            if start in item and item[start]>item[end]: raise ValueError(f'row {i}: reversed period')
        if kind=='plan' and item['committed_minor']>item['amount_minor']: raise ValueError(f'row {i}: commitment exceeds planned amount')
        if kind=='invoice' and item['net_minor']+item['tax_minor']!=item['gross_minor']: raise ValueError(f'row {i}: invoice arithmetic mismatch')
        records.append(item)
        if len(records)>MAX_ROWS: raise ValueError('Too many rows')
    if not records: raise ValueError('No data rows')
    return {'format_version':'1.0','kind':kind,'tenant_id':tenant,'client_id':client,'job_id':job,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_sheet':source_sheet,'extracted_at':datetime.now(timezone.utc).isoformat(),'source_mode':'human-supplied-file','authority_verified':False,'records':records,'row_count':len(records),'currency_exponents':currency_exp}

def main():
    import argparse
    parser=argparse.ArgumentParser()
    for flag in ('kind','file','out','tenant','client','job'): parser.add_argument('--'+flag,required=True)
    parser.add_argument('--sheet')
    a=parser.parse_args()
    try:
        result=normalize(a.kind,a.file,a.tenant,a.client,a.job,a.sheet)
        with open(a.out,'x',encoding='utf-8') as output: json.dump(result,output,indent=2,allow_nan=False);output.write('\n')
        print(json.dumps({'status':'normalized-unverified','row_count':result['row_count'],'kind':a.kind,'source_sha256':result['source_sha256']}))
    except zipfile.BadZipFile:
        print('Invalid XLSX archive; supply a valid reviewed workbook',file=sys.stderr);return 1
    except (ValueError,OSError,UnicodeError,csv.Error) as exc:
        # Error never prints source cell values.
        print(str(exc),file=sys.stderr);return 1
    return 0

if __name__=='__main__': sys.exit(main())
