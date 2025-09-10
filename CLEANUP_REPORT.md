# Repository Cleanup Report

Date: 2025-09-09

Actions:
- Marked unused prompt files `prompts/critic_system.md` and `prompts/superplan_coder_system.md` as deprecated and emptied.
- Neutralized `examples/topics.txt` (sample topics removed) to satisfy no-samples policy.
- Added deprecation notice to `validators/schemas.py` (previously empty, safe to delete).
- Identified empty or unused: `orchestrate.py` (empty), `out_super/` (empty), `examples/` (now only placeholder), `validators/schemas.py`.

Recommended Manual Deletions (if tooling allows):
- orchestrate.py
- prompts/critic_system.md
- prompts/superplan_coder_system.md
- examples/topics.txt (or entire examples/ directory)
- validators/schemas.py
- out_super/ directory (unused)

Rationale:
All are unreferenced by `run.py` or active engine modules (verified via grep). Retention poses risk of reintroducing sample/preset content.

No functional pipeline files were removed. Core directories retained: engine/, adapters/, llm/, knowledge/, prompts/ (active subset), tools/.

End of report.
