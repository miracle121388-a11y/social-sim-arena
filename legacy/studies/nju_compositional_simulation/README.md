# NJU compositional simulation — synthetic engineering prototype

This study wraps the **new independent research kernel**, not the original campus system. Track C is the competition category; Path C describes this technical wrapper. No real validation or live LLM result is claimed.

From `D:\Users\Lenovo\Desktop\njusim-contest`:

```powershell
.\.venv-socioverse\Scripts\python.exe -I -B studies\nju_compositional_simulation\run.py adapter-reproduce-01
```

Choose an unused batch id. The script runs 30 synthetic people for S1/S2/S3, compares every native micro-event against the official wrapper, validates the four official artifact schemas, and saves independent DuckDB panel/Parquet files plus complete sidecar logs under `artifacts/<batch>/`.

Fixed official commit: `9c3ac774816511c121184ca11f539dc398ba1544`; dependency versions: `requirements-socioverse.lock.txt`. These imports are from the independent `vendor/socioverse2`, never the campus repository. Run the custom shared-session factory `build_adapter`; the generic Path-B builder has a different constructor contract.

Exactly one native logical minute per official step, with an initial t=0 record. Native local observations and memory are authoritative; outer panel memory does not feed back a second time. Macro statistics come from native logs. Full microtrace is required for replay: the panel alone is insufficient. `warm_start` and `interaction_rounds>1` are rejected. Synthetic native prefix-intervention tests exist, but this wrapper does not claim official parent-panel branch replay.

Use root `run.py pilot` for training/dev/test experiments and root `run.py test` for mechanism checks. B0 full campus engine and B2 live Jev/LLM remain missing. No credentials, calls, cost, uploads or registration occur in this study.
