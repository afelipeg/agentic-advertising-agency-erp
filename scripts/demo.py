#!/usr/bin/env python3
"""Synthetic offline review pack. No live accounts, approvals or ledger writes."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from agency_tools import run

line={'line_id':'search-1','account_id':'demo-account','supplier_id':'demo-supplier','channel':'search','currency':'MXN','amount_minor':600000,'committed_minor':200000,'start_date':'2026-10-12','end_date':'2026-10-19'}
print(json.dumps({
    'mode':'synthetic-offline-draft',
    'plan_change':run('plan_diff',{'before':[line],'after':[{**line,'amount_minor':500000}]}),
    'budget':run('budget_check',{'currency':'MXN','authorized_minor':1000000,'spent_minor':100000,'open_commitments_minor':200000,'reservations_minor':100000,'requested_minor':500000}),
    'delivery':run('reconcile',{'currency':'MXN','ordered_minor':1000000,'delivered_minor':970000,'invoiced_minor':995000,'tolerance_minor':0}),
    'rebate':run('flat_rebate',{'currency':'MXN','eligible_minor':10000000,'rate_bps':500,'client_share_bps':4000}),
    'next':'Review the revision, reservation and discrepancies. No external changes or payments executed.'
},indent=2))
