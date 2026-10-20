# Source implementation review (2026-10-19)

Reference code cloned/read, not copied into implementation. These are third-party projects, not this project's achievements.

| Repository | inspected commit | license / inspected implementation |
|---|---|---|
| [MINERVA](https://github.com/dcarpintero/minerva) | 4338b88e8bbe36ca760937c97baf1c84aa45e63a | Apache-2.0; agents.py, image_ocr.py, url_checker.py, evaluation.py |
| [ASK Benchmark](https://github.com/megansquire/ask-benchmark) | 7325257141d696d056fc836b01c22f46e4a93523 | MIT; loader, rubric, judge, prepare, analyze, scenario corpus |
| [NVIDIA Financial Fraud Detection](https://github.com/NVIDIA-AI-Blueprints/financial-fraud-detection) | 59492bc700ecd18bbcf9a8e31d78ade0de6a316b | source Apache-2.0; containers separately governed by NVIDIA enterprise/NIM terms; preprocess_TabFormer_np.py and node-prediction notebook |
| [Santander gen-fraud-graph](https://github.com/SantanderAI/gen-fraud-graph) | 8665b9ec44deca10a2e2b7739982be7d00be5834 | Apache-2.0; config, generator, typologies, evaluate |

MINERVA uses RoundRobinGroupChat(max_turns=7), not conditional tool selection. OCR returns a string even on exception. URL expansion issues requests.head on arbitrary supplied URLs with allow_redirects=True, no explicit timeout; reputation POST also has no timeout. We do not copy that access pattern. Its evaluation joins predicted database rows by order and reports accuracy/confidence; those results do not validate this system.

ASK has four clue levels, a 0–4 safety-first rubric, blinded response/key separation and repeated judge agreement analysis. Safety-first scores alone may reward over-warning legitimate activity. This project's reference explicitly penalizes normal-case alarm and scope expansion. Repetition is not sample independence; blind format does not remove all system style clues.

Santander default fraud amount is 9999 versus ordinary uniform 10–500. High hardness jitters by 50% and adds legal decoys, but descriptions remain class-associated and normal/fraud timestamps differ (10:00 vs 12:00). Transaction numbering starts injected records after ordinary count; output folders also separate them. Account IDs are sampled from the account pool, so we do not claim every ID directly reveals labels. Normal decoy cycles defeat naive cycle rules, but cannot remove the other shortcuts. evaluate.py sets ring_fp=acc_fp, mixing account counts with ring_tp; we report ring coverage only.

NVIDIA prepares transaction nodes plus users/merchants, supervised labels and graph train/validation/test sets, then trains SAGEConv embeddings with XGBoost through separate training/inference services. It predicts transaction labels; it does not verify whether a safety instruction applies to a question. Attribution describes model sensitivity, not causation/illegal conduct. We implement a small CPU fixed-neighborhood representation experiment, not a claimed reproduction of their model or GPU pipeline.

## What is actually integrated (2026-10-20)

This is a selection of relevant designs, not a survey of every open-source project or a claim of global superiority. Current web search was unavailable; the source review above is the basis. No third-party benchmark score is attributed to this project.

| Reference idea | Existing implementation | Current evidence and deliberate limit |
|---|---|---|
| MINERVA: gather evidence with tools | Conditional LangGraph planner, allowlisted extraction/guidance/links/comparison/timeline/graph/score tools | Actual image/email tool runs; tool statuses and evidence versions persisted. No arbitrary URL browsing; external reputation remains unavailable. |
| ASK: clue levels, blinded evaluation | 18 authored scenarios with separated latent facts, legitimate counterfactuals; six-system blinded comparison | 36 historical outputs for six stories; normal-case over-warning is a recorded failure, not rewarded as caution. |
| NVIDIA: compare transaction and relationship features | Tabular versus fixed neighbor aggregation with the same classifier and ablation | Real synthetic experiment; no trained GNN reproduction, no real customer fraud detection. Out-of-distribution failure keeps tabular as default. |
| Santander: controlled graph generation | Separate labels, legitimate cycles, time/size splits, extra structural holdout | Actual generated test sets and feature leakage audit; no claim that all leakage has been eliminated. |
| This project's integration | Shared versioned case/evidence/tool/review store, source-scoped advice, bounded repair | New checks bind selected source-span IDs to original text, reject invalid references, and remove specifically unsupported optional content. Same-model auditing remains imperfect. |

The useful combination is a traceable workflow and falsifiable experiments. More components do not automatically improve advice quality. See `RESUME_EVIDENCE.md` for defensible achievements and `../eval/repair-v2/REPORT.md` for the latest failures as well as results.

## Learned graph follow-up

The earlier fixed-neighbor-only description remains the historical implementation. The current follow-up adds independently implemented, trained two-layer mean GraphSAGE using the [SAGEConv operator equation](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.SAGEConv.html), with learned self/neighbor weights and Torch autograd. No PyG or NVIDIA implementation code was copied. This still does not reproduce NVIDIA's heterogeneous transaction-node architecture, XGBoost combination or deployment services. See graph_sage.py and eval/graphsage-v1 for initialization seeds, weights, train/dev/test groups, ablation and structural-challenge failure. The current internal analyst exercise connects graph tools to the same case and review workflow without pretending to be a customer-service investigation of real bank records.
