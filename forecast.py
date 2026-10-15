"""Local scalar Arena response. No server, registration or submission."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace import path,save_json
import argparse,json,math
from datetime import datetime,timezone
from prepare_and_cache import case_features,timestamp
from evaluate import predict,verify_integrity
def respond(request,allow_past=False):
    if request.get("schema_version")!="ssa-agent-api-v2":raise ValueError("Unsupported request schema")
    r=request["round"]
    if r.get("target_type")!="continuous_normal":raise ValueError("Only scalar continuous_normal is implemented")
    if not allow_past and timestamp(r["lock_at"])<=datetime.now(timezone.utc).timestamp():raise ValueError("Deadline passed; use --replay for archived local examples")
    context=r.get("context",{});history=context.get("history",[])
    if len(history)<6:raise ValueError("At least six timestamped historical values required")
    if len({p["date"] for p in history})!=len(history):raise ValueError("Duplicate history dates")
    for p in history:
        datetime.fromisoformat(p["date"])
        if p["date"]>=r["lock_at"][:10] or not math.isfinite(float(p["value"])):raise ValueError("History must precede cutoff")
    history=sorted(history,key=lambda p:p["date"])[-24:]
    pm=context.get("persistence",history[-1]["value"])
    if isinstance(pm,dict):base=pm
    else:base={"mean":float(pm),"sd":float(context.get("persistence_sd",1.5))}
    if not math.isfinite(base["mean"]) or not math.isfinite(base["sd"]) or base["sd"]<=0:raise ValueError("Invalid persistence")
    if abs(history[-1]["value"]-base["mean"])>1e-5:raise ValueError("History/persistence mismatch")
    meta={"round_id":r["round_id"],"series":r.get("series",r["round_id"]),
          "domain":r.get("domain","public-opinion"),"lock_at":r["lock_at"],"release_at":r.get("release_at",r["lock_at"]),
          "baselines":{"persistence":base}}
    case=case_features(meta,{"history":history})
    prediction=predict(case)
    return {"schema_version":"ssa-agent-api-v2","forecast":{"mean":prediction["mean"],"sd":prediction["sd"]}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--request",required=True);p.add_argument("--output",required=True);p.add_argument("--replay",action="store_true");a=p.parse_args()
    verify_integrity()
    request=json.loads(path(a.request).read_text(encoding="utf8"))
    response=respond(request,a.replay);save_json(a.output,response)
    print(json.dumps(response))
if __name__=="__main__":main()
