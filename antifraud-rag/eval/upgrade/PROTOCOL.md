# Upgrade evaluation protocol — registered before development outputs

Base: c3b66b282ae1c9ecca59b192bdf67debaf0ea3e6. No historical trace is rewritten.

Development families: online marketplace seller; routine supplier bank amendment; unpaid invoice repeat request. Held-out families: second-hand machinery seller; school purchasing contractor change; logistics double-payment request; licensed investment clone; national-statistics individual extrapolation; vague material without role. Paraphrases and counterfactuals stay with their family. Security probes are separate, never aggregate as independent customer samples.

Freeze code/configuration after development trial and before held-out invocation. One run per system per family initially; retries/failures retained and reported, not new independent samples. Small author-designed sample does not establish general superiority.

Same Qwen model/temperature, Chinese task, same source snapshot, output token ceiling: direct; all applicable documents; ordinary retrieval+generation; fixed c3b66b2 pipeline; conditional tools. Additional direct-with-identical-observations control. No reference answer enters production retrieval. Multimodal track uses identical extracted observations for text-model comparisons, not an image-capable vs blind-model ranking.

Blind output IDs hide system/configuration. Score separately: task completion/refusal; wrong role/overbroad target; unsupported claim despite real citation; legitimate-case false alarm; omitted essential steps; unsupported specificity on missing data/tool failure; amount containment; counterfactual consistency. Each finding needs a quoted output and source/reference. Review identity: project author/Codex, not bank expert; same-model review not independent ground truth. Automated schema assertions are distinct from semantic review. Measure elapsed time, calls, provider-reported tokens; cost unknown unless dated provider prices verified.

Graph experiments: train time/entity/structure-family disjoint from validation/test, holdout never tuned. Amount and timestamp distributions overlap labels; exclude IDs, descriptions, file/batch metadata from features. Rule, tabular, graph representation plus same classifier, structure removal. Account and edge metrics separately: PR-AUC, precision, recall, FPR, recall at fixed 10% budget. Ring coverage separate denominator. Legitimate high-value settlement cycles retained. Scores are uncalibrated synthetic ranking. Choose simpler default unless development benefit supports complexity, and report held-out regression.

Security probes: prompt injection; URL unavailable/timeout; OCR wrong amount and correction; source region/date/conflict; missing materials; cross-case evidence; stale version; hidden training answers; legitimate cycles; model/evidence disagreement; repeated rejected review. Mock and network runs are labeled separately.
