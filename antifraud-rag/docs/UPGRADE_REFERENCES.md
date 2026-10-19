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
