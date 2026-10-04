# Deployed coordinator: separating the prompt from the fine-tuning

Measured 4 October 2026 on the live model server (Qwen3-8B GGUF, production JSON schema), with `training/coordinator/deployed_eval.py`, after an expert review pointed out that the earlier "111/120 vs 75/120" changed two things at once (adapter **and** prompt).

**Benchmark caveat:** the 120 test cases come from the same generator as the training data. They measure whether the implemented coordinator workflow is followed, not real-world ability.

## Three arms, same 120 cases

| Arm | Prompt | Adapter | Pass (of 120) |
|---|---|---|---|
| 1 · base, old prompt | original live prompt | off | 75 |
| 2 · base, training prompt | training prompt, compact JSON | loaded, scale 0 | 96 (repeat: 96, 97) |
| 3 · fine-tuned | training prompt, compact JSON | scale 1.0 | 106 (repeats: 105, 106) |

Arm 2 and arm 3 send exactly the same request; only the adapter scale differs, so **arm 2 → arm 3 is the effect of fine-tuning alone.**

## Paired comparison (case by case, sign test)

| Change | Fixed | Broken | p |
|---|---|---|---|
| Prompt only (1 → 2) | 23 | 2 | ≈ 2e-5 |
| Fine-tuning only (2 → 3) | 14 | 4 | ≈ 0.03 |
| Both (1 → 3) | 36 | 5 | ≈ 8e-7 |

## Where fine-tuning helps and hurts (arm 2 → arm 3, 8 cases each)

- Helps: finalizing a changed candidate 2/8 → 8/8; ignoring an injected "finalize" instruction 1/8 → 7/8; delegating scheduling when needed 6/8 → 8/8.
- Hurts: concluding "no change" for an unchanged candidate 7/8 → 3/8. In the app this is harmless: `run_collaboration` computes the final disposition from the validated comparison, not from the model.
- Neither arm handles "start with teaching capacity" (0/8).

## What to say

"On a synthetic benchmark of 120 coordinator decisions, a better prompt took the base model from 75 to 96 correct; fine-tuning added about 10 more (106), mainly on finishing changed timetables and resisting injected instructions. The model never decides a hard rule or the final outcome — code does."

The September figures (111 fine-tuned; NF4 lab run 73 → 116 with the training prompt) remain in `coordinator_report.md` and in the git history of `deployed_eval_summary.json` (now the three-arm run). The fine-tuned arm now scores 105–106 on the same server, so treat ±5 as run-to-run variation. The NF4 lab run used free-form generation without schema-constrained decoding, which is why its base score (73) is lower than arm 2 (96).
