# GraphSAGE and internal analyst exercise — actual results

Base commit ea639d7. Protocol was written before training (`PROTOCOL.md`). All transactions and labels are synthetic. This is a follow-up on previously examined distributions, not an untouched external benchmark. No Qwen/embedding/OCR call was needed or rerun for this work.

## Question and method

At a fixed 10% manual account-review budget, does relational information improve ranking? Three separate components are now implemented: explicit task, actual learned GraphSAGE baseline, and case-bound internal analyst exercise.

Nodes are accounts; directed transactions supply in/out statistics, and an undirected adjacency supplies unweighted mean messages. Two learned layers implement W_self*x + W_neighbor*mean(neighbors), hidden width16 with ReLU then a scalar logit. Sigmoid output is an uncalibrated ranking score. No neighbor sampling is needed on these small full-batch graphs. This is a mean GraphSAGE implementation, not GraphRAG, NVIDIA deployment replication or a production detector. Equation reference: https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.SAGEConv.html .

Torch 2.14.1 trained both self/neighbor weights by binary cross entropy; Adam lr.01, weight decay.001, 200 epochs. Train-only standardization and class weight. Checkpoint chosen only by validation AP. Three initialization seeds11/22/33 use the **same** data; mean±sample-standard-deviation measures initialization variability, not a population confidence interval. The default tree remains unchanged; optional demo uses predeclared seed11, not the best test seed. JSON weights have hash verification and numpy inference was checked against actual Torch outputs at every saved checkpoint.

| Split | Disconnected transaction groups | Accounts | Positive-labelled accounts | Transactions |
|---|---:|---:|---:|---:|
| train | 60 | 216 | 102 | 204 |
| dev | 60 | 332 | 107 | 335 |
| test | 60 | 447 | 186 | 486 |

Groups are generated separately by split with distinct accounts, dates and sizes. Entire connected communities remain in one split; no cross-split messages or shared accounts. Labels are separate files and never model input. Labels represent generator-defined anomalous purpose/pattern, not verified crimes. Train/dev/test distributions have related motifs, so group disjointness does not establish full typology independence. The reused2027 shared-hub challenge has360 accounts/180 positives with legitimate and anomalous purposes that can have identical observable structure; do not describe it as newly unseen research data.

## Actual account-level results

AP means `average_precision_score`, not accuracy and not trapezoidal area under a PR curve. Old records named `pr_auc` remain unchanged; new reports use `average_precision`. The node-statistics baseline already includes degree. The ablation removes neighbor messages, not all graph information.

| Model | Original test AP | Recall at45/447 accounts | Structural challenge AP | Recall at36/360 accounts |
|---|---:|---:|---:|---:|
| Node-statistics tree | 0.629 | 15.6% | 0.465 | 8.3% |
| Fixed neighbor mean + tree | 0.882 | 23.1% | 0.519 | 10.6% |
| Two-layer GraphSAGE | 0.915 ± 0.013 | 24.2% ± 0.0pp | 0.496 ± 0.013 | 8.5% ± 1.3pp |
| Neural network without neighbor messages | 0.640 ± 0.018 | 14.9% ± 0.8pp | 0.508 ± 0.009 | 10.2% ± 0.3pp |

This supports a relation-feature benefit on the original synthetic distribution, **not** robust generalisation. GraphSAGE AP near0.496 on the challenge is close to its0.5 positive prevalence; it does not improve over fixed-neighbor features there. All three initializations retrieve45/186 original-test positives in the45-account budget (recall24.2%). This is not “100% fraud accuracy”: all positive labels are synthetic, and most positives are outside the budget. Retain default tree and require explicit model selection.

Full raw predictions,200-epoch histories, checkpoint weights and model/data hashes are in actual/. Reproduction reran actual training and prediction; all22 checkpoint/prediction files matched exactly (`reproduction.json`). Training times in report exclude first Torch import and are not end-to-end service latency claims.

## Product integration

`/api/graph/exercise` creates a synthetic internal-analyst CaseRecord. The existing Agent executes a deterministic task route graph→score→draft, no LLM call claimed. Tool outputs and evidence belong to the same case/version. The model is explicit (tabular or GraphSAGE); selected accounts link to real incident edge IDs within that synthetic case. Questions ask about contracts, funds purpose and legitimate settlement explanations. These questions are project-authored training prompts, not official bank procedures. Labels are not included in the case or tool context.

An ordinary knowledge case is not allowed graph/score, even if supplied graph-shaped fields. A graph_lab marker is **not** authentication: this is local simulation, not a bank access-control system. Model failure yields needs_input without a fabricated shortlist. Case edits invalidate prior review. No account operations or transaction blocking.

Actual browser run **17e0fbba194c4027b036779ccc582317** ranked **4 of 34** synthetic accounts with the exported trained GraphSAGE, used two real local tools and zero model-provider calls, persisted a qualified review, exported the case and rejected stale-version review. Full export/screenshot/assertions in browser/final/. Browser confirmation means review-flow validation, not independent expert validation of ranking utility.

First mobile browser test detected long identifiers overflowing; first screenshot/export and failure are preserved in browser/first-overflow/. CSS wrapping fixed it, repeated actual run passes with no overflow or JavaScript error.

## Checks and boundaries

75 local tests passed, including real Torch training, checkpoint export parity, permutation equivariance, message ablation, whole-group separation, future-edge exclusion, checkpoint tampering, tool eligibility, budget accounting, incident-edge provenance, review/export and version invalidation. Python compilation and frontend syntax checks pass. Torch is optional for inference; CI without it skips the one training test explicitly and still runs inference/integration tests.

Earlier RAG source-review failures are unchanged, not claimed fixed by this graph work. Existing retrieval, amount-containment and legacy tests remain passing. No general superiority over a language model, real fraud rate, bank use or operational efficiency claim. Previous graph reports and runs remain unchanged.
