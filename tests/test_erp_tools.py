"""Regression tests for the ERP circuit calculators.

Worked examples come from docs/erp-reference (media-buying BR-OC-01..05, accounts-jobs job code,
production estimate rules). Amounts are integer minor units.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from agency_tools import run, SCHEMAS, OUTPUT_SCHEMAS, DESCRIPTIONS

BRACKETS = [1000, 2000, 5000, 7000]

def tier(method, base, rates=(200, 300, 500, 700), froms=BRACKETS, amounts=(0, 0, 0, 0), **patch):
    args = dict(currency='MXN', method=method, base_minor=base, reduction_bps=0, deductions_minor=0, flat_bps=0,
                brackets=[dict(from_minor=f, bps=r, amount_minor=m) for f, r, m in zip(froms, rates, amounts)],
                cap_minor=None, prior_adjusted_base_minor=None, client_share_mode='none', client_share_bps=0, client_share_fixed_minor=0)
    args.update(patch)
    return run('tiered_commission', args)


class TieredCommissionTests(unittest.TestCase):
    def test_documented_flat(self):
        r = tier('flat', 1500, brackets=[], flat_bps=500)
        self.assertEqual(r['commission_minor'], 75)

    def test_documented_value_scale(self):
        r = tier('value_scale', 5500, amounts=(100, 250, 350, 500))
        self.assertEqual(r['commission_minor'], 350)
        self.assertEqual(tier('value_scale', 999, amounts=(100, 250, 350, 500))['commission_minor'], 0)

    def test_documented_slab(self):
        for base, expected in ((1500, 30), (3000, 90), (5500, 275), (8000, 560)):
            self.assertEqual(tier('slab', base)['commission_minor'], expected)

    def test_documented_marginal_first_bracket_from_zero(self):
        for base, expected in ((3000, 130), (5500, 200), (8000, 240)):
            r = tier('marginal', base, rates=(500, 300, 200, 100), froms=(0, 2000, 5000, 7000))
            self.assertEqual(r['commission_minor'], expected)

    def test_documented_stepped(self):
        for base, expected in ((3000, 70), (5500, 155), (8000, 300)):
            self.assertEqual(tier('stepped', base)['commission_minor'], expected)
        self.assertEqual(tier('stepped', 500)['commission_minor'], 0)

    def test_cap_reduction_deductions_and_monthly_increment(self):
        r = tier('slab', 10000, reduction_bps=2000, deductions_minor=500, cap_minor=400)
        self.assertEqual(r['adjusted_base_minor'], 7500)
        self.assertEqual(r['commission_minor'], 400)
        self.assertTrue(r['cap_applied'])
        r = tier('slab', 5500, prior_adjusted_base_minor=3000)
        self.assertEqual((r['commission_minor'], r['prior_commission_minor'], r['period_commission_minor']), (275, 90, 185))

    def test_client_share_conserves(self):
        r = tier('slab', 5500, client_share_mode='percent', client_share_bps=3333)
        self.assertEqual(r['client_rebate_minor'] + r['agency_retained_minor'], r['period_commission_minor'])
        r = tier('slab', 5500, client_share_mode='fixed', client_share_fixed_minor=1000)
        self.assertEqual(r['client_rebate_minor'], 275)

    def test_bracket_order_and_flat_misuse(self):
        with self.assertRaises(ValueError):
            tier('slab', 100, froms=(2000, 1000, 5000, 7000))
        with self.assertRaises(ValueError):
            tier('flat', 100)


class PricingTests(unittest.TestCase):
    def test_media_line_cost_types(self):
        base = dict(currency='MXN', rate_minor=1000, measure=20, spots=10, volume=0, package_minor=0)
        self.assertEqual(run('media_line_cost', {**base, 'calc_type': 'per_second'})['gross_minor'], 200000)
        self.assertEqual(run('media_line_cost', {**base, 'calc_type': 'per_thousand', 'volume': 250000})['gross_minor'], 250000)
        self.assertEqual(run('media_line_cost', {**base, 'calc_type': 'package', 'package_minor': 9})['gross_minor'], 9)
        with self.assertRaises(ValueError):
            run('media_line_cost', {**base, 'calc_type': 'per_unit', 'package_minor': 1})

    def test_discount_cascade_compound_vs_additive_and_fee(self):
        args = dict(currency='MXN', gross_minor=100000, mode='compound', discounts_bps=[1000, 500], surcharges=[],
                    fee_base='net', fee_bps=1500, fee_discount_bps=0)
        r = run('discount_cascade', args)
        self.assertEqual(r['net_minor'], 85500)
        self.assertEqual(r['fee_minor'], 12825)
        self.assertEqual(r['client_total_minor'], 98325)
        r = run('discount_cascade', {**args, 'mode': 'additive'})
        self.assertEqual(r['net_minor'], 85000)
        r = run('discount_cascade', {**args, 'surcharges': [dict(kind='percent', value=1000, accumulative=False), dict(kind='percent', value=1000, accumulative=True)]})
        self.assertEqual(r['surcharged_gross_minor'], 121000)
        with self.assertRaises(ValueError):
            run('discount_cascade', {**args, 'mode': 'additive', 'discounts_bps': [6000, 6000]})

    def test_audience_metrics(self):
        r = run('audience_metrics', dict(currency='MXN', net_cost_minor=1000000, universe=1000000,
                                         spots=[dict(spot_id='a', rating_hundredths=500), dict(spot_id='b', rating_hundredths=300)], reach_hundredths=4000))
        self.assertEqual(r['trp_hundredths'], 800)
        self.assertEqual(r['impressions'], 80000)
        self.assertEqual(r['cpr_minor'], 125000)
        self.assertEqual(r['cpm_minor'], 12500)
        self.assertEqual(r['frequency_hundredths'], 20)
        empty = run('audience_metrics', dict(currency='MXN', net_cost_minor=1, universe=1, spots=[], reach_hundredths=None))
        self.assertIsNone(empty['cpr_minor'])

    def test_estimate_totals_direct_and_currency_groups(self):
        line = dict(line_id='l1', kind='indirect', currency='MXN', unit_price_minor=1000, unit_cost_minor=700, quantity=2, days=1,
                    discount_bps=1000, service_eligible=True, supplier_commission_mode='percent', supplier_commission_value=500)
        direct = {**line, 'line_id': 'l2', 'kind': 'direct', 'unit_price_minor': 700, 'discount_bps': 0, 'supplier_commission_mode': 'none'}
        usd = {**line, 'line_id': 'l3', 'currency': 'USD'}
        r = run('estimate_totals', dict(agency_service_bps=1000, agency_service_discount_bps=0, lines=[line, direct, usd]))
        first = r['lines'][0]
        self.assertEqual((first['sale_minor'], first['cost_minor'], first['service_minor'], first['supplier_commission_minor']), (1800, 1400, 180, 70))
        self.assertEqual((r['lines'][1]['service_minor'], r['lines'][1]['margin_minor']), (140, 140))  # direct: agency earns service only
        self.assertEqual(r['invoice_groups'], 2)
        self.assertEqual(r['blockers'], [])
        bad = run('estimate_totals', dict(agency_service_bps=0, agency_service_discount_bps=0, lines=[{**direct, 'unit_price_minor': 900}]))
        self.assertEqual(bad['blockers'][0]['reason'], 'direct_sale_differs_from_cost')

    def test_hourly_fee_overage_conserves_hours(self):
        r = run('hourly_fee_settlement', dict(currency='MXN', instalment_minor=10000000, covered_hours_hundredths=10000,
                                              hours=[dict(person_id='p1', approved_hours_hundredths=8000, client_rate_minor=150000),
                                                     dict(person_id='p2', approved_hours_hundredths=4000, client_rate_minor=100000)],
                                              overage_policy='bill_at_client_rate'))
        self.assertEqual(r['implied_rate_minor'], 100000)
        self.assertEqual(r['overage_hours_hundredths'], 2000)
        self.assertEqual(sum(p['overage_hours_hundredths'] for p in r['per_person']), 2000)
        self.assertEqual(r['overage_minor'], 1333 * 1500 + 667 * 1000)


class FinanceTests(unittest.TestCase):
    def test_payment_terms_rolls_weekends_and_holidays(self):
        r = run('payment_terms', dict(base_date='2026-10-01', term_days=30, rule='net_days', delay_days=0, holidays=['2026-11-02'], weekend_roll=True))
        self.assertEqual(r['due_date'], '2026-11-03')
        r = run('payment_terms', dict(base_date='2026-10-10', term_days=30, rule='end_of_month_then_days', delay_days=7, holidays=[], weekend_roll=True))
        self.assertEqual(r['due_date'], '2026-11-30')
        self.assertEqual(r['expected_date'], '2026-12-07')

    def test_withholding_methods(self):
        base = dict(currency='ARS', method='per_payment', payment_base_minor=100000, accumulated_base_minor=0, accumulated_withheld_minor=0,
                    non_taxable_minimum_minor=20000, rate_bps=200, minimum_withholding_minor=0)
        self.assertEqual(run('withholding', base)['withholding_minor'], 1600)
        r = run('withholding', {**base, 'method': 'cumulative_period', 'accumulated_base_minor': 50000, 'accumulated_withheld_minor': 600})
        self.assertEqual(r['withholding_minor'], 2000)
        r = run('withholding', {**base, 'minimum_withholding_minor': 5000})
        self.assertTrue(r['below_minimum'])
        self.assertEqual(r['withholding_minor'], 0)

    def test_fx_revaluation_signs(self):
        r = run('fx_revaluation', dict(local_currency='MXN', local_exponent=2, closing_rates=[dict(currency='USD', rate_micro=19_000000)],
                                       items=[dict(doc_id='ar1', side='asset', currency='USD', exponent=2, open_minor=10000, book_rate_micro=18_000000),
                                              dict(doc_id='ap1', side='liability', currency='USD', exponent=2, open_minor=10000, book_rate_micro=18_000000)]))
        self.assertEqual(r['items'][0]['gain_loss_minor'], 10000)
        self.assertEqual(r['items'][1]['gain_loss_minor'], -10000)
        self.assertEqual(r['net_minor'], 0)
        with self.assertRaises(ValueError):
            run('fx_revaluation', dict(local_currency='MXN', local_exponent=2, closing_rates=[], items=[dict(doc_id='x', side='asset', currency='USD', exponent=2, open_minor=1, book_rate_micro=1)]))

    def test_aging_buckets(self):
        r = run('aging', dict(as_of='2026-10-31', bucket_limits_days=[30, 60, 90], items=[
            dict(doc_id='a', currency='MXN', due_date='2026-11-15', open_minor=100),
            dict(doc_id='b', currency='MXN', due_date='2026-10-21', open_minor=200),
            dict(doc_id='c', currency='MXN', due_date='2026-06-30', open_minor=300)]))
        c = r['currencies'][0]
        self.assertEqual(c['not_due_minor'], 100)
        self.assertEqual([b['amount_minor'] for b in c['buckets']], [200, 0, 0, 300])
        self.assertEqual(c['buckets'][-1]['to_days'], None)

    def test_allocate_and_installments_conserve(self):
        r = run('allocate', dict(currency='MXN', amount_minor=100, weights=[dict(target_id=x, weight=1) for x in 'abc']))
        self.assertEqual([x['amount_minor'] for x in r['allocations']], [34, 33, 33])
        r = run('allocate', dict(currency='MXN', amount_minor=-100, weights=[dict(target_id=x, weight=1) for x in 'abc']))
        self.assertEqual(r['total_minor'], -100)
        r = run('installment_schedule', dict(currency='MXN', gross_minor=100000, advance_bps=1000, installments=7, start_month='2026-11'))
        self.assertEqual(r['advance_minor'] + sum(i['amount_minor'] for i in r['installments']), 100000)
        self.assertEqual(r['installments'][-1]['month'], '2027-05')

    def test_depreciation_exact_total(self):
        r = run('depreciation_schedule', dict(currency='MXN', cost_minor=100000, residual_minor=1, life_months=36, acquisition_date='2026-10-15', first_month_rule='following_month'))
        self.assertEqual(r['first_month'], '2026-11')
        self.assertEqual(r['months'][-1]['accumulated_minor'], 99999)
        self.assertEqual(r['months'][-1]['net_book_minor'], 1)

    def test_journal_check(self):
        line = dict(line_id='1', account_id='1101', currency='MXN', debit_minor=100, credit_minor=0, required_dimensions_present=True)
        ok = run('journal_check', dict(entry_id='je1', posting_date='2026-10-31', locked_periods=['2026-09'],
                                       lines=[line, {**line, 'line_id': '2', 'debit_minor': 0, 'credit_minor': 100}]))
        self.assertEqual(ok['status'], 'valid')
        bad = run('journal_check', dict(entry_id='je1', posting_date='2026-09-30', locked_periods=['2026-09'], lines=[line]))
        self.assertEqual({e['reason'] for e in bad['errors']}, {'locked_period', 'unbalanced_currency'})

    def test_cash_projection_weighting_overdue_and_horizon(self):
        r = run('cash_projection', dict(as_of='2026-10-05', granularity='week', periods=2, holidays=[],
                                        opening_balances=[dict(currency='MXN', amount_minor=1000)],
                                        items=[dict(item_id='ar1', currency='MXN', direction='in', amount_minor=1000, base_date='2026-09-01', term_days=0, delay_days=0, status='confirmed', probability_bps=10000),
                                               dict(item_id='ar2', currency='MXN', direction='in', amount_minor=1000, base_date='2026-10-12', term_days=0, delay_days=0, status='expected', probability_bps=5000),
                                               dict(item_id='ap1', currency='MXN', direction='out', amount_minor=3000, base_date='2026-10-07', term_days=0, delay_days=0, status='confirmed', probability_bps=10000),
                                               dict(item_id='ap2', currency='MXN', direction='out', amount_minor=9, base_date='2027-01-01', term_days=0, delay_days=0, status='confirmed', probability_bps=10000)]))
        c = r['currencies'][0]
        self.assertEqual(c['overdue_in_minor'], 1000)
        self.assertEqual(c['periods'][0]['closing_minor'], -1000)
        self.assertEqual(c['periods'][1]['in_expected_minor'], 500)
        self.assertEqual(c['beyond_horizon_out_minor'], 9)
        self.assertEqual(c['minimum_closing_minor'], -1000)

    def test_credit_and_invoice_checks(self):
        r = run('credit_exposure', dict(currency='MXN', credit_limit_minor=1000, ar_open_minor=600, approved_unbilled_minor=300, requested_minor=200))
        self.assertTrue(r['requires_override_approval'])
        self.assertEqual(r['headroom_minor'], -100)
        r = run('invoice_check', dict(currency='MXN', lines=[dict(line_id='1', net_minor=1001, vat_bps=1600), dict(line_id='2', net_minor=500, vat_bps=0)],
                                      perceptions_minor=0, other_charges_minor=0, withholdings_netted_minor=0, declared_total_minor=1662, rounding_tolerance_minor=1))
        self.assertEqual(r['vat_minor'], 160)
        self.assertEqual(r['status'], 'rounding_adjustment')


class OperationsTests(unittest.TestCase):
    def test_job_number_rules(self):
        r = run('job_number', dict(client_code='ACM', product_code='01', year=2026, job_type='N', billing_code='F', sequence=7))
        self.assertEqual(r['code'], 'ACM016NF0007')
        self.assertFalse(r['sales_allowed'])
        self.assertIn('typology_forbids_sales', r['warnings'])
        r = run('job_number', dict(client_code='ACM', product_code='01', year=2026, job_type='C', billing_code='?', sequence=1))
        self.assertFalse(r['media_allowed'])
        self.assertFalse(r['client_approval_allowed'])

    def test_spot_match_classes(self):
        ordered = [dict(spot_id='s1', station_id='tv1', air_date='2026-10-12', window_start='20:00', window_end='20:30', material_id='m1'),
                   dict(spot_id='s2', station_id='tv1', air_date='2026-10-12', window_start='21:00', window_end='21:30', material_id='m1'),
                   dict(spot_id='s3', station_id='tv1', air_date='2026-10-12', window_start='22:00', window_end='22:30', material_id='m1')]
        aired = [dict(event_id='e1', station_id='tv1', air_date='2026-10-12', air_time='20:10', material_id='m1'),
                 dict(event_id='e2', station_id='tv1', air_date='2026-10-12', air_time='21:45', material_id='m1'),
                 dict(event_id='e3', station_id='tv1', air_date='2026-10-12', air_time='23:59', material_id='m1')]
        r = run('spot_match', dict(tolerance_minutes=20, match_material=True, ordered=ordered, aired=aired))
        self.assertEqual([(m['spot_id'], m['kind']) for m in r['matches']], [('s1', 'exact'), ('s2', 'tolerance')])
        self.assertEqual(r['ordered_not_aired'], ['s3'])
        self.assertEqual(r['aired_not_ordered'], ['e3'])

    def test_spot_match_ambiguous(self):
        ordered = [dict(spot_id=f's{i}', station_id='r', air_date='2026-10-12', window_start='08:00', window_end='09:00', material_id='m') for i in (1, 2)]
        aired = [dict(event_id=f'e{i}', station_id='r', air_date='2026-10-12', air_time='08:30', material_id='m') for i in (1, 2)]
        r = run('spot_match', dict(tolerance_minutes=0, match_material=True, ordered=ordered, aired=aired))
        self.assertEqual(len(r['ambiguous']), 2)
        self.assertEqual(r['aired_not_ordered'], [])


class ContractTests(unittest.TestCase):
    def test_every_tool_has_contracts_and_description(self):
        self.assertEqual(set(SCHEMAS), set(OUTPUT_SCHEMAS))
        self.assertEqual(set(SCHEMAS), set(DESCRIPTIONS))

    def test_mcp_lists_all_tools(self):
        requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'},
                    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'allocate', 'arguments': {'currency': 'MXN', 'amount_minor': 10, 'weights': [{'target_id': 'a', 'weight': 1}]}}}]
        p = subprocess.run([sys.executable, str(ROOT / 'tools/mcp_server.py')], input='\n'.join(json.dumps(x) for x in requests) + '\n', text=True, capture_output=True, check=True)
        listed, called = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(listed['result']['tools']), len(SCHEMAS))
        self.assertEqual(called['result']['structuredContent']['total_minor'], 10)


class ReviewRegressionTests(unittest.TestCase):
    def test_out_of_range_dates_raise_value_error(self):
        with self.assertRaises(ValueError):
            run('payment_terms', dict(base_date='9999-12-31', term_days=5, rule='net_days', delay_days=0, holidays=[], weekend_roll=True))
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'payment_terms', 'arguments': dict(base_date='9999-12-31', term_days=5, rule='net_days', delay_days=0, holidays=[], weekend_roll=True)}}
        ping = {'jsonrpc': '2.0', 'id': 2, 'method': 'ping'}
        p = subprocess.run([sys.executable, str(ROOT / 'tools/mcp_server.py')], input=json.dumps(request) + '\n' + json.dumps(ping) + '\n', text=True, capture_output=True, check=True)
        first, second = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertTrue(first['result']['isError'])
        self.assertEqual(second['result'], {})

    def test_spot_match_is_order_independent_and_prefers_exact(self):
        spot_a = dict(spot_id='a', station_id='tv', air_date='2026-10-12', window_start='09:31', window_end='10:00', material_id='m')
        spot_b = dict(spot_id='b', station_id='tv', air_date='2026-10-12', window_start='09:00', window_end='09:30', material_id='m')
        aired = [dict(event_id='e1', station_id='tv', air_date='2026-10-12', air_time='09:35', material_id='m')]
        for ordered in ([spot_b, spot_a], [spot_a, spot_b]):
            r = run('spot_match', dict(tolerance_minutes=10, match_material=True, ordered=ordered, aired=aired))
            self.assertEqual(r['matches'], [dict(spot_id='a', event_id='e1', kind='exact')])
            self.assertEqual(r['ordered_not_aired'], ['b'])
        twins = [dict(spot_a, spot_id=x) for x in ('t1', 't2')]
        r = run('spot_match', dict(tolerance_minutes=0, match_material=True, ordered=twins, aired=aired))
        self.assertEqual(len(r['ambiguous']), 2)
        self.assertEqual(r['matches'], [])

    def test_next_fortnight_anchors_before_adding_days(self):
        base = dict(rule='next_fortnight', delay_days=0, holidays=[], weekend_roll=False)
        self.assertEqual(run('payment_terms', dict(base, base_date='2026-01-10', term_days=15))['due_date'], '2026-01-30')
        self.assertEqual(run('payment_terms', dict(base, base_date='2026-01-20', term_days=10))['due_date'], '2026-02-10')

    def test_marginal_equals_stepped_when_first_bracket_is_not_zero(self):
        for base in (3000, 5500, 8000):
            self.assertEqual(tier('marginal', base)['commission_minor'], tier('stepped', base)['commission_minor'])
        self.assertEqual(tier('marginal', 500)['commission_minor'], 0)

    def test_negative_period_gives_no_client_rebate(self):
        r = tier('slab', 3000, prior_adjusted_base_minor=5500, client_share_mode='percent', client_share_bps=5000)
        self.assertEqual((r['period_commission_minor'], r['client_rebate_minor'], r['agency_retained_minor']), (-185, 0, -185))

    def test_additive_cascade_never_goes_negative(self):
        r = run('discount_cascade', dict(currency='MXN', gross_minor=1, mode='additive', discounts_bps=[5000, 5000], surcharges=[], fee_base='none', fee_bps=0, fee_discount_bps=0))
        self.assertEqual(r['net_minor'], 0)
        self.assertEqual(sum(x['amount_minor'] for x in r['steps']), 1)

    def test_depreciation_spreads_remainder(self):
        r = run('depreciation_schedule', dict(currency='MXN', cost_minor=5, residual_minor=0, life_months=10, acquisition_date='2026-01-01', first_month_rule='acquisition_month'))
        self.assertEqual(max(m['charge_minor'] for m in r['months']), 1)
        self.assertEqual(r['months'][-1]['accumulated_minor'], 5)

    def test_aging_accepts_credit_balances(self):
        r = run('aging', dict(as_of='2026-10-31', bucket_limits_days=[30], items=[dict(doc_id='inv', currency='MXN', due_date='2026-10-01', open_minor=500), dict(doc_id='cn', currency='MXN', due_date='2026-10-01', open_minor=-200)]))
        c = r['currencies'][0]
        self.assertEqual(c['buckets'][0]['amount_minor'], 300)
        self.assertEqual(c['weighted_days_overdue'], 30)

    def test_journal_check_reports_many_errors(self):
        line = dict(line_id='x', account_id='a', currency='MXN', debit_minor=1, credit_minor=1, required_dimensions_present=False)
        lines = [dict(line, line_id=f'l{i}') for i in range(500)]
        r = run('journal_check', dict(entry_id='je', posting_date='2026-10-31', locked_periods=['2026-10'], lines=lines))
        self.assertEqual(r['status'], 'invalid')


if __name__ == '__main__':
    unittest.main()
