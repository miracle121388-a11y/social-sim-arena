"""Arena v1: selective historical calibration and conservative normal forecasting.
Pure numerical code. No filesystem/network access. All hyperparameters here.
"""
import numpy as np
from scipy.special import ndtr,logsumexp
CONFIG = {'scale_prior': 2, 'location': 'persistence', 'selector': 'cdf', 'budget': 8, 'eta': 2.0, 'shrink': 1.0, 'decay': 0.0, 'stop': 0.0, 'update': 'crps', 'robust': 0.0}

def crps(mu,sd,y):
    z=(y-mu)/sd
    return sd*(z*(2*ndtr(z)-1)+2*np.exp(-.5*z*z)/np.sqrt(2*np.pi)-1/np.sqrt(np.pi))

def prior(config):
    loc=config["location"];k=config["scale_prior"]
    a=np.ones((6,4))
    if loc=="persistence":a[0,:]*=8.
    elif loc=="trend":a[3:5,:]*=4.
    elif loc=="smooth":a[[1,2,5],:]*=4.
    if k>=0:a[:,k]*=6.
    return a.flatten()/a.sum()

def cdf_value(w,means,sds,p):
    grid=np.linspace(float(np.min(means-5*sds)),float(np.max(means+5*sds)),129)
    f=ndtr((grid[None,:]-means[:,None])/sds[:,None])
    q=float(w@p)
    cov=(w*p)@f-q*(w@f)
    return float(np.trapezoid(cov*cov,grid)/max(q*(1-q),1e-10))

def mean_value(w,means,sds,p):
    q=float(w@p);cov=float((w*p)@means-q*(w@means))
    return cov*cov/max(q*(1-q),1e-10)

def forecast(case,reveal,config=None,policy=None,budget=None):
    cfg=dict(CONFIG if config is None else config)
    if policy is not None:cfg["selector"]=policy
    if budget is not None:cfg["budget"]=budget
    m=np.asarray(case["means"]);s=np.asarray(case["sds"]);w=prior(cfg)
    pool=case["pool"];chosen=[];trace=[];spent=0.
    rng=np.random.default_rng(case["seed"])
    while len(chosen)<cfg["budget"]:
        ids=[i for i,r in enumerate(pool) if i not in chosen and spent+r["cost"]<=cfg["budget"]]
        if not ids:break
        scores=[]
        for i in ids:
            r=pool[i];p=1-ndtr((r["threshold"]-np.asarray(r["means"]))/np.asarray(r["sds"]))
            if cfg["selector"]=="recent":v=1/(1+r["age"])
            elif cfg["selector"]=="random":v=float(rng.random())
            elif cfg["selector"]=="mean":v=mean_value(w,m,s,p)
            elif cfg["selector"]=="entropy":
                q=float(w@p);v=-q*np.log(max(q,1e-12))-(1-q)*np.log(max(1-q,1e-12))
            else:v=cdf_value(w,m,s,p)
            v*=np.exp(-cfg["decay"]*r["age"])/r["cost"]
            scores.append(v)
        j=int(np.argmax(scores));i=ids[j]
        if scores[j]<=cfg["stop"]:break
        r=pool[i];y=float(reveal(i));chosen.append(i);spent+=r["cost"]
        em=np.asarray(r["means"]);es=np.asarray(r["sds"])
        if cfg["update"]=="binary":
            p=1-ndtr((r["threshold"]-em)/es)
            ll=np.log(np.maximum(p if y>r["threshold"] else 1-p,1e-8))
        else:
            loss=crps(em,es,y)/max(.25,float(np.median(es)))
            # Bounded score influence limits damage from historical outliers.
            if cfg["robust"]>0:loss=np.minimum(loss,cfg["robust"])
            ll=-loss
        ll*=cfg["eta"]*np.exp(-cfg["decay"]*r["age"])
        lw=np.log(np.maximum(w,1e-300))+ll
        w=np.exp(lw-logsumexp(lw))
        trace.append({"index":i,"utility":float(scores[j]),"spent":spent})
    # Projection is scored as normal; CDF acquisition is a surrogate after projection.
    mean=float(w@m);var=float(w@(s*s+m*m)-mean*mean)
    base=case["persistence"];a=cfg["shrink"]
    mean_out=(1-a)*base["mean"]+a*mean
    second=(1-a)*(base["sd"]**2+base["mean"]**2)+a*(var+mean*mean)
    sd_out=max(.05,float(np.sqrt(max(0.,second-mean_out**2))))
    return {"mean":float(mean_out),"sd":sd_out,"cost":spent,"selected":chosen,"trace":trace,"ess":float(1/(w@w))}
