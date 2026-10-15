"""Frozen Arena v1 evaluator; scalar normal CRPS and temporal-block inference."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace import path,save_json,digest
import argparse,json,hashlib,math,copy,importlib.util
from datetime import datetime
import numpy as np
from scipy.special import ndtr
import method

SEED=20261015
def crps(mu,sd,y):
    z=(y-mu)/sd
    return float(sd*(z*(2*ndtr(z)-1)+2*math.exp(-.5*z*z)/math.sqrt(2*math.pi)-1/math.sqrt(math.pi)))
def verify_integrity():
    lock=json.loads(path("infrastructure.arena_v1.lock.json").read_text(encoding="utf8"))
    for n,h in lock["files"].items():
        if digest(n)!=h:raise ValueError("Frozen file changed: "+n)
    return True
def cases(split):
    return [r for r in json.loads(path("data/arena_v1/cache.json").read_text(encoding="utf8")) if r["split"]==split]
def public_state(r):
    pool=[{k:v for k,v in e.items() if k!="target"} for e in r["records"]]
    seed=SEED+int(hashlib.sha256(r["id"].encode()).hexdigest()[:8],16)
    return {"id":r["id"],"series":r["series"],"domain":r["domain"],
            "lock_at":r["lock_at"],"means":r["means"],"sds":r["sds"],
            "persistence":r["persistence"],"pool":pool,"seed":seed}
def predict(r,config=None,policy=None,budget=None):
    state=public_state(r);seen=[]
    limit=(config or method.CONFIG)["budget"] if budget is None else budget
    def reveal(i):
        if type(i) not in (int,np.int64,np.int32) or i<0 or i>=len(r["records"]):raise ValueError("invalid query")
        if i in seen:raise ValueError("duplicate query")
        if len(seen)+1>limit:raise ValueError("query budget exceeded")
        assert r["records"][i]["id"]<r["lock_at"][:10]
        seen.append(int(i));return r["records"][i]["target"]
    out=method.forecast(copy.deepcopy(state),reveal,config,policy,budget)
    assert out["selected"]==seen
    assert abs(out["cost"]-len(seen))<1e-8 and out["cost"]<=limit
    assert math.isfinite(out["mean"]) and math.isfinite(out["sd"]) and out["sd"]>0
    return out
def row(r,p):
    loss=crps(p["mean"],p["sd"],r["outcome"])
    b=r["persistence"];bl=crps(b["mean"],b["sd"],r["outcome"])
    date=datetime.fromisoformat(r["lock_at"].replace("Z","+00:00"));week=f"{date.isocalendar().year}-W{date.isocalendar().week:02}"
    z=abs(r["outcome"]-p["mean"])/p["sd"]
    return {"id":r["id"],"series":r["series"],"domain":r["domain"],"week":week,
            "mean":p["mean"],"sd":p["sd"],"outcome":r["outcome"],"crps":loss,
            "normalized_crps":loss/b["sd"],"persistence_crps":bl,
            "skill":1-loss/bl if bl>0 else 0.,"mae":abs(p["mean"]-r["outcome"]),
            "cover80":float(z<=1.2815515655446004),"cover95":float(z<=1.959963984540054),
            "cost":p.get("cost",0),"selected":p.get("selected",[]),"ess":p.get("ess",None)}
def summarize(rows):
    weeks=sorted(set(r["week"] for r in rows))
    blocks=[float(np.mean([r["normalized_crps"] for r in rows if r["week"]==w])) for w in weeks]
    return {"n":len(rows),"n_weeks":len(weeks),"primary":float(np.mean(blocks)),
            "mean_crps":float(np.mean([r["crps"] for r in rows])),
            "mean_skill":float(np.mean([r["skill"] for r in rows])),
            "mae":float(np.mean([r["mae"] for r in rows])),
            "coverage80":float(np.mean([r["cover80"] for r in rows])),
            "coverage95":float(np.mean([r["cover95"] for r in rows])),
            "mean_cost":float(np.mean([r["cost"] for r in rows])),
            "domain_loss":{d:float(np.mean([r["normalized_crps"] for r in rows if r["domain"]==d])) for d in sorted(set(r["domain"] for r in rows))},
            "week_losses":dict(zip(weeks,blocks))}
def run(split,config=None,policy=None,budget=None):
    records=[row(r,predict(r,config,policy,budget)) for r in cases(split)]
    return {"summary":summarize(records),"rows":records}
def baselines(split):
    rs=cases(split);result={}
    for name in ["persistence","ewma","trend","climatology"]:
        rows=[row(r,r["official_baselines"][name]) for r in rs if name in r["official_baselines"]]
        if len(rows)==len(rs):result["official_"+name]={"summary":summarize(rows),"rows":rows}
    for i in range(24):
        rows=[row(r,{"mean":r["means"][i],"sd":r["sds"][i]}) for r in rs]
        result[f"expert_{i:02}"]={"summary":summarize(rows),"rows":rows}
    uniform={"scale_prior":-1,"location":"uniform","selector":"recent","budget":0,"eta":1.,"shrink":1.,"decay":0.,"stop":0.,"update":"crps","robust":0.}
    result["uniform"]=run(split,uniform)
    uniform["budget"]=12
    result["all_evidence_crps"]=run(split,uniform)
    return result
def paired(a,b):
    # b minus a, resampled by whole calendar-week blocks.
    ar={r["id"]:r for r in a["rows"]};br={r["id"]:r for r in b["rows"]}
    assert ar.keys()==br.keys()
    weeks=sorted(set(r["week"] for r in ar.values()))
    delta=np.array([np.mean([br[k]["normalized_crps"]-ar[k]["normalized_crps"] for k in ar if ar[k]["week"]==w]) for w in weeks])
    rng=np.random.default_rng(SEED)
    boot=delta[rng.integers(0,len(delta),size=(4000,len(delta)))].mean(1)
    return {"mean_control_minus_full":float(delta.mean()),"ci95":np.quantile(boot,[.025,.975]).tolist(),"n_blocks":len(weeks),"adjusted_for_multiple_comparisons":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--split",choices=["train","dev","test"],default="dev");p.add_argument("--final",action="store_true");p.add_argument("--output",required=True);a=p.parse_args()
    verify_integrity()
    if a.split=="test":
        if not a.final:raise ValueError("test requires frozen final run")
        frozen=json.loads(path("provenance/arena_v1/frozen.json").read_text())
        assert frozen["method_sha256"]==digest("method.py")
        if path("provenance/arena_v1/test_release.json").exists():raise FileExistsError("test already released")
        save_json("provenance/arena_v1/test_release.json",{"method_sha256":digest("method.py"),"warning":"retrospective holdout, public outcomes"})
    out={"split":a.split,"method_sha256":digest("method.py"),"config":method.CONFIG,"Full":run(a.split)}
    if a.final:
        controls=baselines(a.split)
        controls["NoEvidence"]=run(a.split,budget=0)
        for name in ["recent","random","mean","entropy","cdf"]:controls["selector_"+name]=run(a.split,policy=name)
        cfg=dict(method.CONFIG,shrink=1.);controls["NoShrink"]=run(a.split,cfg)
        cfg=dict(method.CONFIG,robust=0.);controls["NoRobust"]=run(a.split,cfg)
        out["controls"]=controls;out["paired"]={n:paired(out["Full"],v) for n,v in controls.items()}
        out["budget_curves"]={str(b):run(a.split,budget=b) for b in [0,2,4,8,12]}
    save_json(a.output,out);print(json.dumps({"output":a.output,"summary":out["Full"]["summary"]}))
if __name__=="__main__":main()
