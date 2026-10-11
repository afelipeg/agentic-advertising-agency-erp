import csv
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from normalize_files import normalize,TEMPLATES

class FileTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.dir=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def row(self):
        return dict(tenant_id='t',client_id='c',job_id='j',line_id='l',account_id='a',supplier_id='s',channel='search',currency='MXN',currency_exponent='2',amount_minor='100000',committed_minor='50000',start_date='2026-10-12',end_date='2026-10-19')
    def csvfile(self,rows,headers=None):
        p=self.dir/'input.csv'
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=headers or list(TEMPLATES['plan']));w.writeheader();w.writerows(rows)
        return p
    def test_scoped_normalization_unverified(self):
        result=normalize('plan',self.csvfile([self.row()]),'t','c','j')
        self.assertEqual(result['row_count'],1);self.assertFalse(result['authority_verified']);self.assertEqual(result['records'][0]['amount_minor'],100000)
        self.assertEqual(len(result['source_sha256']),64)
    def test_reject_scope_duplicate_unknown_and_decimal(self):
        for rows,headers in [([{**self.row(),'client_id':'other'}],None),([self.row(),self.row()],None),([{**self.row(),'email':'secret@example.com'}],list(TEMPLATES['plan'])+['email']),([{**self.row(),'amount_minor':'1,000.00'}],None)]:
            with self.assertRaises(ValueError):normalize('plan',self.csvfile(rows,headers),'t','c','j')
    def test_errors_do_not_echo_cells(self):
        with self.assertRaises(ValueError) as e:normalize('plan',self.csvfile([{**self.row(),'line_id':'=reveal-secret'}]),'t','c','j')
        self.assertNotIn('reveal-secret',str(e.exception))
    @unittest.skipUnless(importlib.util.find_spec('openpyxl'),'optional XLSX dependency unavailable')
    def test_xlsx_formula_and_multisheet_rejected(self):
        import openpyxl
        p=self.dir/'input.xlsx';book=openpyxl.Workbook();sheet=book.active;sheet.title='Approved'
        sheet.append(list(TEMPLATES['plan']));sheet.append(list(self.row().values()));book.save(p)
        self.assertEqual(normalize('plan',p,'t','c','j')['row_count'],1)
        book.create_sheet('Other');book.save(p)
        with self.assertRaisesRegex(ValueError,'sheet'):normalize('plan',p,'t','c','j')
        self.assertEqual(normalize('plan',p,'t','c','j','Approved')['row_count'],1)
        sheet['J2']='=1+1';book.save(p)
        with self.assertRaisesRegex(ValueError,'Formula'):normalize('plan',p,'t','c','j','Approved')

if __name__=='__main__':unittest.main()
