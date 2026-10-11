import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from agency_tools import run,strict_json,SCHEMAS,OUTPUT_SCHEMAS,validate
from mcp_server import handle

class ToolTests(unittest.TestCase):
    def test_concurrent_requests_require_updated_balance(self):
        args=dict(currency='MXN',authorized_minor=1000000,spent_minor=0,open_commitments_minor=0,reservations_minor=0,requested_minor=600000)
        self.assertTrue(run('budget_check',args)['within_budget'])
        second=run('budget_check',{**args,'reservations_minor':600000})
        self.assertFalse(second['within_budget']);self.assertEqual(second['after_request_minor'],-200000)

    def test_delivery_mismatch_and_shortfall(self):
        r=run('reconcile',dict(currency='MXN',ordered_minor=1000000,delivered_minor=970000,invoiced_minor=995000,tolerance_minor=0))
        self.assertEqual(r['discrepancy_minor'],25000);self.assertEqual(r['status'],'hold');self.assertIn('short_delivery',r['reasons'])
        r=run('reconcile',dict(currency='MXN',ordered_minor=100,delivered_minor=90,invoiced_minor=90,tolerance_minor=0))
        self.assertEqual(r['status'],'hold')

    def test_full_match_and_approved_tolerance(self):
        r=run('reconcile',dict(currency='JPY',ordered_minor=100,delivered_minor=100,invoiced_minor=101,tolerance_minor=1))
        self.assertEqual(r['status'],'matched')

    def test_rebate_conservation_and_rounding(self):
        r=run('flat_rebate',dict(currency='MXN',eligible_minor=10000000,rate_bps=500,client_share_bps=4000))
        self.assertEqual((r['rebate_minor'],r['client_return_minor'],r['agency_retained_minor']),(500000,200000,300000))
        r=run('flat_rebate',dict(currency='USD',eligible_minor=1,rate_bps=5000,client_share_bps=5000))
        self.assertEqual(r['client_return_minor']+r['agency_retained_minor'],r['rebate_minor'])

    def test_profit_separates_managed_spend(self):
        r=run('margin',dict(currency='USD',agency_revenue_minor=100,agency_cost_minor=200,managed_spend_minor=1000000))
        self.assertEqual(r['margin_minor'],-100);self.assertEqual(r['margin_bps'],-10000)
        self.assertIsNone(run('margin',dict(currency='USD',agency_revenue_minor=0,agency_cost_minor=2,managed_spend_minor=100))['margin_bps'])

    def test_strict_inputs_and_json(self):
        args=dict(currency='MXN',eligible_minor=10,rate_bps=500,client_share_bps=0)
        for patch in ({'eligible_minor':True},{'rate_bps':500.0},{'currency':'mxn'},{'rate_bps':10001},{'extra':1}):
            with self.assertRaises(ValueError):run('flat_rebate',{**args,**patch})
        with self.assertRaisesRegex(ValueError,'client_share_bps'):run('flat_rebate',{'currency':'MXN'})
        for raw in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):strict_json(raw)

    def test_digest_changes_but_cannot_approve(self):
        a=run('payload_digest',{'payload':{'revision':2,'amount':100}})
        b=run('payload_digest',{'payload':{'amount':100,'revision':2}})
        c=run('payload_digest',{'payload':{'amount':101,'revision':2}})
        self.assertEqual(a,b);self.assertNotEqual(a['sha256'],c['sha256']);self.assertFalse(a['authorizes_execution'])

    def line(self,**patch):
        return dict(line_id='tv-1',account_id='a',supplier_id='s',channel='tv',currency='MXN',amount_minor=500000,committed_minor=400000,start_date='2026-10-12',end_date='2026-10-19',**patch)

    def test_committed_line_removal_blocks(self):
        r=run('plan_diff',{'before':[self.line()],'after':[]})
        self.assertEqual(r['status'],'blocked');self.assertEqual(r['currency_deltas'][0]['delta_minor'],-500000)
        self.assertEqual(r['blockers'][0]['reason'],'commitment_removed')

    def test_commitment_cannot_be_rewritten(self):
        line=self.line()
        r=run('plan_diff',{'before':[line],'after':[{**line,'committed_minor':0,'amount_minor':100}]})
        self.assertIn('commitment_rewritten',[x['reason'] for x in r['blockers']])

    def test_currency_transfer_not_netted(self):
        line={**self.line(),'committed_minor':0}
        r=run('plan_diff',{'before':[line],'after':[{**line,'currency':'USD'}]})
        self.assertEqual(len(r['currency_deltas']),2);self.assertTrue(r['requires_host_approval'])

    def test_invalid_plan_ids_and_dates(self):
        line=self.line()
        for before in ([line,line],[{**line,'start_date':'2026-02-30'}],[{**line,'amount_minor':1}]):
            with self.assertRaises(ValueError):run('plan_diff',{'before':before,'after':[]})

    def test_mcp_stdio_transport_and_invalid_tool(self):
        requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'send_money','arguments':{}}}]
        p=subprocess.run([sys.executable,str(ROOT/'tools/mcp_server.py')],input='\n'.join(json.dumps(x) for x in requests)+'\n',text=True,capture_output=True,check=True)
        results=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(results),3);self.assertEqual(len(results[1]['result']['tools']),len(SCHEMAS));self.assertTrue(results[2]['result']['isError'])
        for tool in results[1]['result']['tools']:self.assertTrue(tool['annotations']['readOnlyHint']);self.assertIn('outputSchema',tool)

    def test_output_schema_rejects_extra_fields(self):
        with self.assertRaises(ValueError):validate({'currency':'USD','rebate_minor':1,'client_return_minor':0,'agency_retained_minor':1,'extra':1},OUTPUT_SCHEMAS['flat_rebate'])

if __name__=='__main__':unittest.main()
