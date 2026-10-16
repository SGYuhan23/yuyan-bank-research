import unittest
from datetime import date
from copy import deepcopy
from model import build, curve, money

class BusinessChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=build()
    def test_every_cash_path_reconciles(self):
        cases=[(c['opening_fen'],c['events'],c['result']) for c in self.d['fuling']['clients']]
        cases += [(self.d['supplier']['opening_fen'],s['events'],s['result']) for s in self.d['supplier']['scenarios']]
        for opening,events,r in cases:
            self.assertEqual(r['end_balance_fen'],opening+sum(x['amount_fen'] for x in events))
            for row in r['daily']:
                self.assertEqual(row['balance_fen'],opening+sum(x['amount_fen'] for x in events if x['date']<=row['date']))
    def test_first_supplier_cash_problem_precedes_receivable(self):
        s=self.d['supplier']['scenarios'][0]
        self.assertEqual(s['result']['first_gap_date'],'2027-01-15')
        self.assertLess(s['result']['first_gap_date'],self.d['supplier']['contract']['acceptance'])
        self.assertEqual(s['result']['peak_gap_fen'],money(56))
        self.assertEqual(s['result']['negative_days'],(date(2027,4,19)-date(2027,1,15)).days)
    def test_receipt_of_bill_does_not_add_cash(self):
        s=self.d['supplier']['scenarios'][1]
        self.assertEqual(next(x['balance_fen'] for x in s['result']['daily'] if x['date']=='2027-04-19'),money(-56))
        self.assertEqual(s['result']['negative_days'],185)
    def test_discount_replaces_not_duplicates_maturity_cash(self):
        s=self.d['supplier']['scenarios'][2]
        self.assertEqual(len([e for e in s['events'] if e['amount_fen']>0]),1)
        self.assertNotIn('2027-07-19',[e['date'] for e in s['events']])
        self.assertEqual(s['fee_fen'],662795)
        self.assertEqual(s['result']['end_balance_fen'],money(40)-662795)
        self.assertEqual(s['result']['peak_gap_fen'],money(56))
    def test_advance_already_in_opening_not_added_again(self):
        s=self.d['supplier']['scenarios'][0]
        self.assertEqual(sum(e['amount_fen'] for e in s['events'] if e['amount_fen']>0),money(96))
        self.assertEqual(s['result']['end_balance_fen'],money(40))
    def test_delay_changes_duration_not_peak(self):
        a,b=self.d['supplier']['scenarios'][0],self.d['supplier']['scenarios'][3]
        self.assertEqual(a['result']['peak_gap_fen'],b['result']['peak_gap_fen'])
        self.assertEqual(b['result']['negative_days']-a['result']['negative_days'],14)
        for old,new in zip(a['events'][:4],b['events'][:4]):self.assertEqual(old,new)
    def test_regional_clients_are_not_identical_balance_scalings(self):
        a,b,c=self.d['fuling']['clients']
        self.assertEqual(a['result']['peak_gap_fen'],money(90))
        self.assertEqual(b['result']['peak_gap_fen'],0)
        self.assertEqual(c['result']['peak_gap_fen'],money(36))
        self.assertLess(c['result']['first_gap_date'],a['result']['first_gap_date'])
        self.assertEqual(self.d['fuling']['stress']['negative_days'],205)
    def test_capacity_has_real_deferral(self):
        f=self.d['fuling'];p=f['plan'];byid={c['id']:c for c in f['clients']}
        self.assertGreater(sum(c['hours'] for c in f['clients']),f['capacity_hours'])
        self.assertEqual(sum(byid[i]['hours'] for i in p['selected']),p['used_hours'])
        self.assertEqual(p['used_hours']+p['reserve_hours'],f['capacity_hours'])
        self.assertEqual(p['deferred'],['F02'])
    def test_simulation_not_claimed_as_cash_fact(self):
        all_events=[e for c in self.d['fuling']['clients'] for e in c['events']]
        all_events += [e for s in self.d['supplier']['scenarios'] for e in s['events']]
        self.assertTrue(all(e['status']=='PROJECTED' and e['layer']=='ASSUMPTION' for e in all_events))
    def test_duplicate_event_and_hidden_out_of_window_payment_rejected(self):
        e=self.d['supplier']['scenarios'][0]['events'][0]
        with self.assertRaises(AssertionError):curve(money(35),[e,e],'2027-01-01','2027-07-31')
        with self.assertRaises(AssertionError):curve(money(35),[e],'2027-02-01','2027-07-31')

if __name__=='__main__':unittest.main(verbosity=2)
