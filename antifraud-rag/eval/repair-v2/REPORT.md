# Integration repair results — 2026-10-20

Base: 511358aec7a82c5a78d5ae550ace27aec66a62d2, branch codex/antifraud-tools-upgrade. This batch is development/follow-up evidence, not an independent benchmark. The old six-story heldout is now a regression set. Same Qwen provider, one output per condition; no real customer data or banking deployment.

## Changes and root causes

1. Positive BM25 results could omit the required source. New Agent auto checks identified core tasks against their applicable source IDs, performs one real semantic expansion if missing, logs the reason and returned IDs, then reassesses sufficiency. Explicit BM25/semantic modes remain explicit. The original legacy workflow retains zero-hit-only fallback.
2. Literal certainty phrases rejected negation. Remove that substring check; semantic review distinguishes a claim from its denial. This is not a universal certainty detector.
3. Reviewer output sometimes includes a positive `other` scene or an empty questions-array audit. Accept only harmless positive rows for actually requested/empty fields; missing real output checks, negative rows and unrelated scenes still fail.
4. Broad same-model review missed unsupported follow-up questions. New focused check reviews every item, chooses a source-span ID and binds the verbatim source programmatically. It verifies completeness and valid references. One contract retry, one answer repair; optional unsupported items can be removed, while core coverage is rechecked. No fixed answer substitution.

Early development produced malformed review JSON, invented/ellipsized quotations and false rejections. All first attempts remain in dev/, history-*/ and followup-v1/. Failed contracts are not counted as successful semantic detection. The final history-v3 review returned specific substantive issues for both known bad answers.

## Retrieval (real embeddings)

`retrieval-actual.json`: six authored development questions, 18 searches (three modes per question), top-3 target-source hit count:

| Mode | Target source found |
|---|---:|
| BM25 | 3/6 |
| auto zero-hit fallback | 5/6 |
| semantic | 6/6 |

Queries used the real embedding endpoint; document vectors may reuse their hash-keyed cache, query embeddings were live. These are source recall counts, not answer accuracy. The extra coverage check is separate: machinery-sale query initially retrieved bec-guidance and bec-case, logged `task_source_missing_despite_positive_hits`, then actually retrieved receipt-guidance by semantic search. First run 15317071a3c54d9388dcb061793c41b7 later failed on a redundant empty-field review. After that specific contract repair, new run ef404937250b4522a3ce5771ba223cf1 returned pending_review. Neither output replaces the other.

## Same-task follow-up versus all-source single-turn baseline

`followup-v2/freeze.json` records code hashes and six prompts before execution. This is a new development batch, not external validation. A subsequent harmless-empty-review repair is separately exercised by the coverage and browser runs; the six frozen outputs were not silently relabelled as reruns of that change.

| Observed metric | Tool Agent | Same-model all-source baseline |
|---|---:|---:|
| Tasks | 6 | 6 |
| Generated outputs | 5 pending review | 6 returned |
| Explicit insufficient-evidence stop | 1 | 1 output explains missing evidence |
| Chat calls | 38 | 6 |
| Median elapsed time | 76.17 s | 3.64 s |
| Elapsed range | 6.35–93.11 s | 2.53–4.95 s |

No efficiency improvement is established. Concurrency, provider latency and a small sample limit timing conclusions. Token monetary costs are not calculated from unverified prices.

Source comparison by Codex (not an independent bank expert) accepted seller and separated-comparison outputs; rejected three generated outputs for revision. Persisted records are in `followup-v2/source-reviews.json`:

- Normal change: correctly acknowledges prior telephone verification and has no stamp/password/unique-account questions, but “诈骗高发信号” asserts unprovided frequency and adds an unsupported normal-change explanation.
- Unpaid maintenance bill: preserves the premise and same-payment restriction, but omits explicit email search for account-change requests and asks about an assumed current account request/payment notice.
- Investment: registration/licensing safety limits are correct, but the URL question omits “if a website URL is listed in the register”.
- Unsupported internal freeze-policy request stops rather than inventing a policy. Counted separately, not as an accepted generated answer.

The all-source baseline also has defects: seller response adds calling the buyer as an independent-verification requirement; normal response says the already completed telephone verification is insufficient without a source for that assertion; unpaid response lacks the explicit do-not-repeat-until-investigated condition. No overall superiority claim is made.

## Historical failure checks

`history-v3/history-normal.json` identifies unsupported unique-account, stamp/password and contract-consistency questions. `history-v3/history-email.json` identifies unrelated payment-history questions and unsupported risk categorisation. Both return substantive issues (2/2 selected historical examples), not merely schema failures. This is targeted regression evidence, not a general detection rate.

## Tests and browser

- 64 offline tests pass, including actual local persistence/state tests plus mocked network/error tests; `tests-actual.txt` is the raw result. New checks cover source span binding, invalid cross-source IDs, missing review rows, partial-hit fallback routing, semantic unavailability, explicit BM25 preservation and optional review-row handling.
- Python compileall and both frontend JS syntax checks pass.
- Real local browser: actual model result, acceptance record, export, then version edit invalidates prior review. Files in browser/ include export, screenshot and assertions; new run f743ba56c8c84bccb35b9f72126614ee. Browser acceptance is a workflow test, not an expert endorsement of every sentence.
- First browser run 835bb6ace762426088b5db4168dd3c87 failed with provider HTTP 400; raw failure retained. One immediate retry hit server-start connection refusal; after readiness check the browser test completed. The cause of provider HTTP 400 is not established.
- Original amount-containment regression remains in the passing suite. Training and graph experiments are previously executed evidence, not newly rerun here.

## Acceptance boundary

The integrated workflow, source coverage expansion, reproducible records, targeted history checks and local demonstration are implemented. Semantic acceptance is incomplete: same-model review still misses conditions and can approve unsupported wording. This is a resume-ready **exploratory engineering project with measured limitations**, not a bank-ready answer-quality guarantee. No merge to main or deployment is part of this work.
