"""Independent receipts and score audit; does not select or change the method."""
from pathlib import Path
import sys,json,hashlib,math,importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workspace import path,digest,save_json
import evaluate as ev
import numpy as np
def main():
    ev.verify_integrity()
    f=json.loads(path("provenance/arena_v1/frozen.json").read_text())
    assert digest("method.py")==f["method_sha256"]
    logs=json.loads(path("provenance/arena_v1/search.json").read_text())
    assert len(logs)==24 and [r["trial"] for r in logs]==list(range(1,25))
    controls=json.loads(path("results/arena_v1/dev-controls.json").read_text())
    guard=controls["official_persistence"]["summary"]["domain_loss"]
    best=json.loads(path("results/arena_v1/initial.json").read_text())["summary"]["primary"]
    for r in logs:
        i=r["trial"];assert digest(f"provenance/arena_v1/candidates/{i:02}.py")==r["method_sha256"]
        result=json.loads(path(f"results/arena_v1/dev-{i:02}.json").read_text())
        assert result["method_sha256"]==r["method_sha256"]
        s=result["Full"]["summary"];keep=s["primary"]<best-1e-6 and all(v<=1.5*guard[k]+1e-12 for k,v in s["domain_loss"].items())
        assert r["status"]==("KEEP" if keep else "REVERT")
        if keep:best=s["primary"]
    assert abs(best-f["dev_primary"])<1e-12
    # Read official scoring as an independent comparator, never execute original project.
    spec=importlib.util.spec_from_file_location("official_score",path("provenance/arena_v1/upstream/ssa__scoring.py"));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    count=0
    for split in ["dev","test"]:
        d=json.loads(path(f"results/arena_v1/{split}-final.json").read_text())
        assert d["method_sha256"]==f["method_sha256"]
        groups=[d["Full"],*d["controls"].values(),*d["budget_curves"].values()]
        for g in groups:
            assert ev.summarize(g["rows"])==g["summary"]
            for r in g["rows"]:
                assert abs(mod.crps_normal(r["mean"],r["sd"],r["outcome"])-r["crps"])<1e-10
                assert r["sd"]>0 and len(r["selected"])==len(set(r["selected"]))
                count+=1
    report={"status":"passed","trials":24,"kept":f["kept"],"official_score_rows_verified":count,"locked_files_verified":len(json.loads(path("infrastructure.arena_v1.lock.json").read_text())["files"]),
      "method_sha256":f["method_sha256"],"limitations":["Only 4 calendar-week blocks per split; intervals exploratory.",
      "Dev and test include adjacent days in week 38; no temporal embargo was preregistered.",
      "No prospective Arena submissions; normalized-loss gain does not imply positive mean skill.",
      "Expert bank has no social mechanism simulator; selection is historical validation compute."]}
    save_json("provenance/arena_v1/validation.json",report)
    print(json.dumps(report))
if __name__=="__main__":main()
