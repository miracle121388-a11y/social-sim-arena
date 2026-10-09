# Independent research workspace

Read PROJECT_CONTEXT.md, STATUS.md, DECISIONS.md, SESSION_HANDOFF.md, CLAIMS.md and experiments/registry.csv before starting a new session.

SOURCE_ROOT = D:\Users\Lenovo\Desktop\NJU-xianlinSWM is ALWAYS READ ONLY. No source execution/import, installs, tests, builds, Git mutations, DB connections, services, notifications, or source-directory logs. Source already has user changes; never reset or restore them.

RESEARCH_ROOT = D:\Users\Lenovo\Desktop\njusim-contest is the only write workspace. All commands must explicitly set cwd here. Resolve destination paths; reject links, junctions, hard links and paths outside this directory. Never use a worktree or branch of the original repo. Keep environment/cache/temp/DB/log paths here. Do not change source ACLs: this could affect the user's concurrent work. Process-local audit hooks are defense in depth, not an OS sandbox.

Frozen legacy_snapshot files must remain byte-identical. Check provenance/reuse_manifest.json. Code belongs in src/njusim; contest wrapper in studies/nju_compositional_simulation. Do not edit official vendor core.

Use `.\.venv\Scripts\python.exe -I -B run.py test` for native tests; `run.py all --batch <new-id>` for a synthetic smoke and pilot. Use the separate `.venv-socioverse` and scripts/verify_adapter.py for the optional wrapper. No default network or API key. External paid models, real student data, registration, upload, publishing and contacting anyone require a new explicit user instruction.

Preserve one research question: shared mechanism calibration with observable process and closed-loop trajectory constraints, tested on independent events and held-out compositions. Do not declare personality, modularity, memory, calibration or a larger model inherently novel/effective. B0/B2 missing means missing; never substitute a rewrite or offline fixture under their names.

Record failed runs as well as successful runs. Never edit existing traces to improve results. Distinguish proposed / implemented / tested_synthetic / validated_real. No validated_real claim currently exists. Verify source integrity after key phases with scripts/isolation.py; report differences without reverting them. End by updating facts, status, decisions, claims, registry and handoff.
