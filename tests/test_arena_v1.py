"""Scientific contracts for temporal inputs, budget and distribution utility."""
from pathlib import Path
import sys,unittest,copy,importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import method
import evaluate as ev
from prepare_and_cache import expert_bank
class Contracts(unittest.TestCase):
 def test_official_score(self):
  p=Path(__file__).resolve().parents[1]/"provenance/arena_v1/upstream/ssa__scoring.py"
  spec=importlib.util.spec_from_file_location("official_scoring",p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  for mu,sd,y in [(0,1,0),(40,2,35),(-10,.2,-12),(1,4,3)]:
   self.assertAlmostEqual(ev.crps(mu,sd,y),mod.crps_normal(mu,sd,y),places=12)
 def test_no_target_state(self):
  for r in ev.cases("dev"):
   state=ev.public_state(r)
   self.assertNotIn("outcome",state)
   self.assertTrue(all("target" not in p for p in state["pool"]))
 def test_future_target_invariance(self):
  r=ev.cases("dev")[0];other=copy.deepcopy(r);other["outcome"]=1e9
  self.assertEqual(ev.predict(r),ev.predict(other))
 def test_budget_and_unique(self):
  for r in ev.cases("dev")[:3]:
   for pol in ["cdf","recent","random","mean","entropy"]:
    out=ev.predict(r,policy=pol,budget=4)
    self.assertLessEqual(out["cost"],4);self.assertEqual(len(out["selected"]),len(set(out["selected"])))
 def test_deterministic(self):
  r=ev.cases("dev")[0]
  self.assertEqual(ev.predict(r,policy="random",budget=8),ev.predict(r,policy="random",budget=8))
 def test_cdf_detects_scale_only_disagreement(self):
  w=np.array([.5,.5]);mu=np.array([0.,0.]);sd=np.array([1.,3.]);p=np.array([.1,.9])
  self.assertEqual(method.mean_value(w,mu,sd,p),0.)
  self.assertGreater(method.cdf_value(w,mu,sd,p),.01)
 def test_cdf_identity(self):
  from scipy.special import ndtr
  w=np.array([.3,.7]);mu=np.array([-1.,2.]);sd=np.array([1.,2.]);p=np.array([.2,.8])
  x=np.linspace(min(mu-5*sd),max(mu+5*sd),129);f=ndtr((x[None,:]-mu[:,None])/sd[:,None])
  q=w@p;f0=(w*(1-p)/(1-q))@f;f1=(w*p/q)@f;fbar=w@f
  direct=np.trapezoid(q*(f1-fbar)**2+(1-q)*(f0-fbar)**2,x)
  self.assertAlmostEqual(method.cdf_value(w,mu,sd,p),direct,places=12)
 def test_temporal_cutoff(self):
  for r in ev.cases("dev"):
   self.assertTrue(all(p["date"]<r["lock_at"][:10] for p in r["history"]))
   self.assertTrue(all(p["id"]<r["lock_at"][:10] for p in r["records"]))
 def test_positive_scales_short_history(self):
  m,s=expert_bank([{"date":"2026-01-01","value":4}],1)
  self.assertTrue(np.all(np.isfinite(m)));self.assertTrue(np.all(s>0))
 def test_persistence_fallback(self):
  r=ev.cases("dev")[0];cfg=dict(method.CONFIG,shrink=0.,budget=0);p=ev.predict(r,cfg)
  self.assertAlmostEqual(p["mean"],r["persistence"]["mean"])
  self.assertAlmostEqual(p["sd"],r["persistence"]["sd"])
if __name__=="__main__":unittest.main()
