# Upgrade verification ledger

## 当前收尾状态

最新收尾验证见[final-closeout-v1/REPORT.md](../eval/final-closeout-v1/REPORT.md)：80项本地回归、真实Qwen与embedding、浏览器审核闭环；mock、历史回放与实时工具分开记录。图实验数据和模型未更改。以下历史实验保留原版本背景。

Evaluation is an exploratory small-sample comparison, not a bank pilot. Code/source and reference requirements were fixed before held-out runs (`eval/upgrade/PROTOCOL.md`, `cases.json`, batch `freeze.json`). Development paraphrases remain development, training hidden answers never enter the five-document official index. Six held-out stories are six independent designed families, not 36 independent customers. One run per system/family; all failures retained.

## References and scope

See UPGRADE_REFERENCES.md for actual reviewed commits and licenses. Implementation is independent; no third-party performance is claimed. Graph representation is fixed mean-neighbor aggregation plus HistGradientBoosting, not trained GraphSAGE. It allows a controlled structure-removal comparison with the identical classifier. Local generated model score is an experimental ranking, not a calibrated probability.

## Development failures retained

`eval/upgrade/dev/` preserves every trial, including unknown tool arguments, source aliases used in place of evidence IDs, extraneous planner JSON fields, repeated tool calls, requests for unavailable attachments, and excessive clarification. The fixes specify current tool schemas, constrain availability, separate planner/output instructions, and reuse existing source-scoped generation/validation. Program assigns actual evidence IDs. These are local fixes, not a generic semantic guarantee.

`training-failed-first.json` records a real same-model semantic-review failure; `training-actual.json` records the subsequent real run with zero-based verbatim turn checking. The deterministic training client is deliberately limited to authored facts; it does not invent unrestricted customer dialogue.

## Graph split and leakage limits

Base train/dev/test: separate account IDs, 2024/2025/2026 times, graph sizes 3–4/5–6/7–8. These are topology-size families within related motif types, **not** complete typology isolation. An additional 2027 held-out two-loop shared-hub family was therefore evaluated without retraining or selecting on it (`graph/structural-heldout-*`). It includes visually identical legitimate and anomalous purpose; topology alone cannot distinguish them. This explicitly tests missing business context.

Amounts use the same label-independent distribution, timestamps share label-independent distributions within each split. Feature allowlist excludes IDs, filenames, batch/row order, text descriptions and labels. Labels are separate files. The leakage audit is a designed-feature inspection plus actual ranges and disjointness checks, not proof against every possible shortcut. All graph data are synthetic.

Default remains tabular despite a development gain for neighbor representation: a single small generated dataset does not establish reliable gain. Account/transaction PR-AUC, threshold precision/recall/FPR and top-10% review-budget recall are separate; ring coverage is count/count, with no account false-positive denominator. Trade-off and OOD failures are retained.

## Verification categories

- Offline unit/integration tests: real SQLite/Decimal/training state plus separately mocked failures. These do not prove online model quality.
- Actual OCR: native Vision on a project-authored payment-text image, bounding locations retained. It recognized text; it did not verify payment.
- Actual URL adapter: local domain parsing, reputation unavailable without credentials. A live external reputation result is **not verified**.
- Actual Qwen development and held-out records: usage and calls logged, no hidden reasoning. Prices not verified; monetary cost is unknown. Embedding usage is not fully instrumented, so reported token totals are chat-provider usage only.
- Browser: real HTTP operations, model execution, persisted review, export and version invalidation; screenshots are evidence of local UI, not deployment.
- Old `runs/`: unchanged historical behavior; not automatically attributed to new tools.

Same-model blind grading is auxiliary; system names/configurations are hidden but output style can identify a workflow. Project-author/Codex source review is not an independent bank expert audit. Quoted findings and uncertainties take precedence over a single aggregate score.

## Actual result summary and acceptance limits

54 offline tests passed (see `tests-actual.txt` for exact run count); Python compilation and both JS syntax checks passed. Browser tests exercise actual HTTP, live model result, local review, export and invalidation. The initial browser trial failed due to malformed option tags and a GET/POST mismatch; both were corrected, then rerun. Latest UI translates execution labels and marks planner suggestions as not executed until tool results return.

Frozen text track: [36 output records and comparison](../eval/upgrade/heldout-v1/REPORT.md). New tool workflow: 1/6 generated, 2/6 clarified/limited, 3/6 failed. Direct/all-documents return more answers but not necessarily supported answers. These results do **not** demonstrate higher answer accuracy. Preserve auto semantics: BM25 zero-hit fallback works on original colloquial questions; partial positive hits can still miss the necessary source.

Material-tool track: actual image extraction→guidance and email extraction→compare/timeline/links→guidance succeeded after dependency scheduling repair. Native OCR worked. Links returned partial/unavailable reputation truthfully. A malicious email instruction did not execute code or produce a safety guarantee. The email's generated follow-up question still mixed in payment-history checking and was **rejected by source review**. Normal account-change demo also returned pending-review but invented “唯一有效账户/盖章/密语” questions; it was **rejected**, with real persistent Review records. These runs prove workflow connectivity, not semantic acceptance.

M1 versioning/review and core M2 tool routing are implemented and exercised; M3 authored dialogue and bounded review are implemented; M4 synthetic experiment is run with failure on unseen structure. M5 fair comparison and evidence packaging are complete, but **normal-case generation quality has not passed full acceptance**. Therefore keep the original project name and do not claim the whole upgrade is verified. External reputation, non-macOS OCR, independent human/bank expert evaluation and real banking use remain unverified; PDF extraction, trained GNN, enterprise auth and actual transaction operations are not implemented.

Final integration audit also bound graph-sample and training-session entrypoints to the shared CaseRecord/Evidence/ToolResult store; previously their standalone local results were not case-bound. `graph/shared-case-actual.json` and `training-case-actual.json` are actual persisted runs after the fix; two ownership/provenance integration tests cover it. This does not change the frozen knowledge-model comparison or claim a rerun.

## Follow-up repair evidence

Latest [repair-v2 report](../eval/repair-v2/REPORT.md) supersedes the earlier runtime-completion counts only for its explicitly named new development batch. 64 offline tests pass. Actual six-query retrieval is BM25 3/6, auto 5/6 and semantic 6/6 target-source hits; separate Agent coverage expansion retrieves the missing receipt source after positive irrelevant hits. Two old bad answers produce substantive focused-review issues. Six new Agent tasks produce five pending-review outputs and one evidence-limited stop, but source comparison rejects three of the generated outputs. No general answer-accuracy or efficiency improvement is established. Same-model checks remain imperfect; independent expert evaluation is still unavailable.

## Trained graph follow-up

See [graphsage-v1](../eval/graphsage-v1/REPORT.md). Actual trained two-layer model, seeds11/22/33 and neural no-message ablation. Original account test AP mean0.915±0.013, extra shared-hub challenge0.496±0.013. The three runs vary model initialization on fixed data; they are not independent datasets/confidence intervals. Comparators and every seed prediction are retained. Whole connected groups, accounts and times are separate by split; this is not proof of full typology isolation. 22 checkpoint/prediction files exactly reproduced in a second real training run. 75 local tests, including optional Torch training, and actual GraphSAGE browser exercise with review/export/stale rejection pass. First mobile-overflow failure retained. No online Qwen/embedding/OCR rerun or new claim of overall answer-quality superiority.
