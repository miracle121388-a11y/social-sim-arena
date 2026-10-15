"""24 bounded method-only trials; sources/decisions retained, no destructive Git reset."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace import path,save_json,digest,ROOT
import json,subprocess,hashlib,re,copy,datetime

def plans():
    return [
      ("forecast","Uniform statistical experts",dict(location="uniform",scale_prior=-1,shrink=1.)),
      ("forecast","Persistence-focused narrow uncertainty",dict(location="persistence",scale_prior=0,shrink=1.)),
      ("forecast","Persistence-focused empirical uncertainty",dict(location="persistence",scale_prior=1,shrink=1.)),
      ("forecast","Persistence-focused wider uncertainty",dict(location="persistence",scale_prior=2,shrink=1.)),
      ("forecast","Smoothed forecasts with baseline shrinkage",dict(location="smooth",scale_prior=1,shrink=.5)),
      ("forecast","Damped trends with baseline shrinkage",dict(location="trend",scale_prior=1,shrink=.5)),
      ("forecast","Narrow forecast with half baseline weight",dict(location="persistence",scale_prior=0,shrink=.5)),
      ("forecast","Conservative empirical forecast",dict(location="persistence",scale_prior=1,shrink=.25)),
      ("acquisition","Four recent historical validations",dict(selector="recent",budget=4)),
      ("acquisition","Eight recent historical validations",dict(selector="recent",budget=8)),
      ("acquisition","All twelve historical validations",dict(selector="recent",budget=12)),
      ("acquisition","Random eight validations",dict(selector="random",budget=8)),
      ("acquisition","CDF utility with four validations",dict(selector="cdf",budget=4)),
      ("acquisition","CDF utility with eight validations",dict(selector="cdf",budget=8)),
      ("acquisition","Mean utility with eight validations",dict(selector="mean",budget=8)),
      ("acquisition","Response entropy with eight validations",dict(selector="entropy",budget=8)),
      ("robustness","Slow proper-score learning",dict(eta=.25)),
      ("robustness","Moderate proper-score learning",dict(eta=.5)),
      ("robustness","Fast proper-score learning",dict(eta=2.)),
      ("robustness","Bounded influence of old forecast errors",dict(robust=1.)),
      ("robustness","Binary posterior update consistent with binary utility",dict(update="binary")),
      ("robustness","Recency decay for regime changes",dict(decay=.15)),
      ("robustness","Stop if distribution value is small",dict(selector="cdf",stop=.005)),
      ("robustness","Stronger baseline shrinkage",dict(shrink=.35))]
def evaluate(i):
    filename=f"results/arena_v1/dev-{i:02}.json"
    p=subprocess.run([sys.executable,"-I","-B","evaluate.py","--split","dev","--output",filename],cwd=ROOT,capture_output=True,text=True,timeout=90)
    path(f"provenance/arena_v1/candidates/{i:02}.log").write_text(p.stdout+p.stderr,encoding="utf8")
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    return json.loads(path(filename).read_text(encoding="utf8"))
def main():
    import evaluate as ev
    ev.verify_integrity()
    plan=plans();assert len(plan)==24
    save_json("provenance/arena_v1/plans.json",plan)
    base=path("method.py").read_text(encoding="utf8")
    initial=copy.deepcopy(ev.method.CONFIG);best_config=initial.copy()
    controls=ev.baselines("dev")
    save_json("results/arena_v1/dev-controls.json",controls)
    strong=min(controls,key=lambda n:controls[n]["summary"]["primary"])
    init=ev.run("dev",initial);best=init["summary"]["primary"]
    save_json("results/arena_v1/initial.json",init)
    guard=controls["official_persistence"]["summary"]["domain_loss"]
    log=[];stage=None;anchor=None
    for i,(st,h,changes) in enumerate(plan,1):
        if st!=stage:
            stage=st;anchor=best_config.copy()
            if st in ("acquisition","robustness"):anchor["shrink"]=max(.5,anchor["shrink"])
            if st=="robustness" and not anchor["budget"]:anchor.update(budget=8,selector="cdf")
        cfg=(initial.copy() if st=="forecast" else anchor.copy());cfg.update(changes)
        source=re.sub(r"^CONFIG = .*?$","CONFIG = "+repr(cfg),base,flags=re.M)
        path("method.py").write_text(source,encoding="utf8")
        path(f"provenance/arena_v1/candidates/{i:02}.py").write_text(source,encoding="utf8")
        row={"trial":i,"stage":st,"hypothesis":h,"config":cfg,"method_sha256":digest("method.py")}
        try:
            d=evaluate(i);s=d["Full"]["summary"]
            safe=all(v<=1.5*guard[k]+1e-12 for k,v in s["domain_loss"].items())
            keep=safe and s["primary"]<best-1e-6
            row.update(status="KEEP" if keep else "REVERT",metrics=s,guard=safe)
            if keep:best=s["primary"];best_config=cfg.copy()
        except Exception as exc:row.update(status="FAILED",error=str(exc))
        log.append(row);save_json(f"provenance/arena_v1/candidates/{i:02}.json",row)
        # Restore only owned method bytes after every trial.
        path("method.py").write_text(re.sub(r"^CONFIG = .*?$","CONFIG = "+repr(best_config),base,flags=re.M),encoding="utf8")
        ev.verify_integrity()
        print(json.dumps({"trial":i,"status":row["status"],"primary":row.get("metrics",{}).get("primary"),"best":best}),flush=True)
    if any(r["status"]=="FAILED" for r in log):
        save_json("provenance/arena_v1/search-errors.json",log)
        raise RuntimeError("Trials failed; no silent replacement or test release")
    save_json("provenance/arena_v1/frozen.json",{"method_sha256":digest("method.py"),"config":best_config,"dev_primary":best,"initial_primary":init["summary"]["primary"],"dev_selected_strong_control":strong,"strong_control_primary":controls[strong]["summary"]["primary"],"trials":24,"kept":sum(r["status"]=="KEEP" for r in log),"frozen_at":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    save_json("provenance/arena_v1/search.json",log)
if __name__=="__main__":main()
