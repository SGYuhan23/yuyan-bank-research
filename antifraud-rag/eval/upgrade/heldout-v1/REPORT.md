# Frozen comparison results

Six authored held-out story families, one run per system (36 outputs); not 36 independent users. Qwen settings and source snapshot in freeze.json. Runtime completion is not answer accuracy. `needs_input` includes correct refusal of unsupported individual probability and correct role clarification.

| System | Generated result | Failures | Clarification/limitation | Chat calls | Total seconds | Chat input/output tokens |
|---|---:|---:|---:|---:|---:|---:|
| direct | 6/6 | 0 | 0 | 6 | 17.3 | 2503/627 |
| all | 6/6 | 0 | 0 | 6 | 27.0 | 29965/867 |
| retrieved | 5/6 | 1 | 0 | 5 | 121.8 | 13208/777 |
| fixed | 2/6 | 4 | 0 | 15 | 168.7 | 53554/5027 |
| tools | 1/6 | 3 | 2 | 26 | 174.6 | 62707/6994 |
| same_observations | 6/6 | 0 | 0 | 6 | 24.2 | 19135/826 |

No claim of superiority: tool workflow has lower generation completion, higher latency/calls, and source review still finds unsupported questions. Useful product differences are real adapters, evidence/version binding and persisted rejection, not demonstrated higher QA accuracy. All-documents is a strong low-complexity baseline on five units, but source review finds unsupported internal-process instructions and a 2.18-billion vs 2.18-亿 error. Same-observations also invents “bank arrival enquiry number (BSB/Account Number)”.

`author-source-review.json` contains 12 source-checked findings across all six families; all quotes checked against raw outputs. Author is Codex/project author, non-blind, not a bank specialist. `blind.json` excludes system/configuration and `key.json` is separate. `grade-*.json` is same-model auxiliary scoring; `auxiliary-summary.json` is **not a validated accuracy table**. The judge missed the BSB mistake and statistics amount error. Some quote checks remain uncertain. Do not use its totals as independent performance evidence.

Known failures: BM25 partial positive hits can prevent semantic fallback despite missing the needed source; old certainty phrase check can reject a negated phrase; review schema/coverage can fail. These were not tuned on the held-out questions. Monetary cost is unknown; usage counts cover chat calls, not all embedding tokens. No production/customers/business uplift.

After this frozen comparison, a separate material-tool trial found a dependency scheduling bug: a valid batch containing extraction and dependent tools was rejected. The controller was repaired to execute extraction first then independent remainder. That repair was prompted by the tool track, not these held-out answers. Frozen scores describe the prior recorded hash; latest scheduler is separately regression tested, not silently treated as a fresh held-out run. No held-out corpus was edited.
