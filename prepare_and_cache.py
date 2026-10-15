"""Pinned public-release replay adapter. Fixed during Arena v1 method search.
No target labels enter forecast state. Archived snapshots are retrospective,
not certified historical first-vintage data and not prospective predictions.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace import path,save_json,digest
import json, math, hashlib
from datetime import datetime
import numpy as np

def timestamp(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()

def expert_bank(history, horizon=1.):
    """24 fixed statistical experts: six locations times four scales."""
    y=np.asarray([p["value"] for p in history],float)
    if not len(y): raise ValueError("history required")
    last=y[-1]
    differences=np.diff(y[-13:])
    scale=max(.25,float(np.sqrt(np.mean(differences**2)))) if len(differences) else 1.5
    # Robust floor and horizon inflation use history only.
    scale*=math.sqrt(max(1.,min(float(horizon),3.)))
    def ewma(a):
        m=y[max(0,len(y)-12)]
        for v in y[-11:]:m=a*v+(1-a)*m
        return m
    def trend(n):
        v=y[-n:];x=np.arange(len(v),dtype=float)
        if len(v)<3:return last
        slope=float(np.dot(x-x.mean(),v-v.mean())/np.dot(x-x.mean(),x-x.mean()))
        return last+np.clip(slope*horizon,-2*scale,2*scale)
    centers=np.array([last,ewma(.4),ewma(.7),trend(4),trend(8),.75*last+.25*np.median(y[-8:])])
    means=np.repeat(centers,4)
    sds=np.tile(np.array([.5,1.,1.5,2.])*scale,6)
    return means,np.maximum(.2,sds)

def case_features(r,lock):
    h=sorted(lock["history"],key=lambda p:p["date"])
    # Same maximum 24 history points as the official scalar agent envelope.
    h=h[-24:]
    cadence=np.median([max(1,(datetime.fromisoformat(b["date"])-datetime.fromisoformat(a["date"])).days) for a,b in zip(h,h[1:])]) if len(h)>1 else 7.
    # Forecast NEXT publication; avoid field-date/release-date confusion.
    horizon=1.
    mu,sd=expert_bank(h,horizon)
    records=[]
    # Historical rolling validation is computation, not purchase of new real information.
    for j in range(max(5,len(h)-12),len(h)):
        pm,ps=expert_bank(h[:j],1.)
        records.append({"id":h[j]["date"],"means":pm.tolist(),"sds":ps.tolist(),
                        "threshold":float(h[j-1]["value"]),"target":float(h[j]["value"]),
                        "age":len(h)-1-j,"cost":1.})
    return {"id":r["round_id"],"series":r["series"],"domain":r["domain"],
            "lock_at":r["lock_at"],"release_at":r["release_at"],
            "history":h,"means":mu.tolist(),"sds":sd.tolist(),"records":records,
            "scale":float(max(.25,np.median(sd))),"cadence_days":float(cadence),
            "persistence":r["baselines"]["persistence"],
            "official_baselines":r["baselines"]}

def main():
    dest=path("data/arena_v1/cache.json")
    if dest.exists():raise FileExistsError("Frozen cache already exists")
    d=json.loads(path("provenance/arena_v1/upstream/site-data.json").read_text(encoding="utf8"))
    accepted=[];excluded=[]
    for r in d["rounds"]:
        if not (r.get("target_type")=="continuous_normal" and r.get("domain") in ("public-opinion","consumer") and r.get("status")=="resolved" and r.get("scoreable",True)):continue
        name="provenance/arena_v1/upstream/locks/"+r["round_id"]+".json"
        p=path(name);reason=[]
        if not p.exists():excluded.append({"id":r["round_id"],"reasons":["missing lock"]});continue
        l=json.loads(p.read_text(encoding="utf8"));h=l.get("history",[]);res=r.get("resolution",{})
        if l.get("corrected") or res.get("corrected"):reason.append("post-hoc correction flagged")
        if timestamp(l["observed_at"])>timestamp(r["lock_at"]):reason.append("late snapshot")
        if len(h)<6:reason.append("fewer than six observations")
        if not h or any(p["date"]>=r["lock_at"][:10] for p in h):reason.append("nonhistorical dates")
        if h and abs(float(h[-1]["value"])-float(r["baselines"]["persistence"]["mean"]))>1e-5:reason.append("history/persistence mismatch")
        if "value" not in res:reason.append("missing scalar resolution")
        if reason:excluded.append({"id":r["round_id"],"reasons":reason});continue
        case=case_features(r,l);case["outcome"]=float(res["value"]);case["resolved_at"]=res["resolved_at"]
        case["split"]="train" if r["lock_at"]<"2026-08-25" else "dev" if r["lock_at"]<"2026-09-16" else "test"
        accepted.append(case)
    accepted.sort(key=lambda r:(r["lock_at"],r["id"]))
    save_json("data/arena_v1/cache.json",accepted)
    counts={s:sum(r["split"]==s for r in accepted) for s in ["train","dev","test"]}
    save_json("provenance/arena_v1/data-audit.json",{"counts":counts,"excluded":excluded,
              "accepted_ids":{s:[r["id"] for r in accepted if r["split"]==s] for s in counts},
              "cache_sha256":digest("data/arena_v1/cache.json"),
              "limitations":["Previously public outcomes; retrospective holdout only.","Lock timestamps are upstream assertions, not independently verified historical commits.",
              "Historical validation points use the lock-time vintage; no claim those values were first-vintage at their own historic origin.",
              "Cost is one rolling validation record over a fixed 24-expert bank; cached access is a proxy, not web/API expense.",
              "No LLM, no private student data, no registration or submission."]})
    print(json.dumps({"counts":counts,"excluded_n":len(excluded)}))
if __name__=="__main__":main()
