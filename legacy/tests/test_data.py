import unittest
from njusim.data_protocol import validate_observed_rows

class DataProtocolTests(unittest.TestCase):
    def row(self):
        return dict(event_id='e',participant_id='pseudonym',stage='join',opportunity_id='o',window_start='2026-10-01T09:00:00+08:00',window_end='2026-10-01T09:01:00+08:00',feature_as_of='2026-10-01T08:00:00+08:00',label=None,observed=False,censored=True,provenance='synthetic',evidence_id='source-1',consent_ref='')
    def test_missing_realistic_row_stays_missing(self):
        self.assertIsNone(validate_observed_rows([self.row()])[0]['label'])
    def test_real_requires_explicit_authorization(self):
        r=self.row();r.update(provenance='real_observed',consent_ref='approved-protocol')
        with self.assertRaises(PermissionError):validate_observed_rows([r])
    def test_missing_cannot_be_silently_zero(self):
        r=self.row();r['label']=0
        with self.assertRaises(ValueError):validate_observed_rows([r])
    def test_future_feature_rejected(self):
        r=self.row();r['feature_as_of']='2026-10-02T08:00:00+08:00'
        with self.assertRaises(ValueError):validate_observed_rows([r])
