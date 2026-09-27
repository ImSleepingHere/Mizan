# Request interpreter evaluation (spec §18.2, §18.7)

- `handwritten_test.jsonl`: 30 real professor requests with expected interpretations, approved and **frozen on 2026-09-27** (SHA-256 `74f827453cdfff631fc0942aa106fc73c3a0de8e34fdd17889a384158c1ae868`, checked by `tests/test_interpreter.py` and the eval script). Never used for training or prompt work. Scored **once**, at the end of items 1–4.
- `dev_set.py` → `dev.jsonl`: 40 development cases written by Claude in its own wording. Prompt and rule work uses only this set.
- `scoring.py`: strict exact match (headline), per-field accuracy, silent guesses (an expected unsupported code missing) and false flags, split by Arabic / English / mixed.
- `eval_interpreter.py --set dev` or `--set test --final` (needs the local model on port 11435). The test run refuses to run twice or on a modified file.

Test context: `requester_role` professor, own sections S087–S091, today 2026-09-27 (Sunday). Rules: finding a slot is in scope whatever the date wording (`date_note` when a date is mentioned); booking on a date is EXTRA_SESSION or DATED_CHANGE.

Caveat: the prompt author also wrote the test expectations, so the test set is not blind to the author; it is blind to prompt iteration.

## Result (scored once, 2026-09-27, base Qwen3-8B, no adapter)

| | Strict | Silent-guess cases | False flags |
|---|---|---|---|
| All (30) | 7 | 3 | 1 |
| Arabic (19) | 5 | 2 | 0 |
| English (6) | 1 | 0 | 1 |
| Mixed (5) | 1 | 1 | 0 |

Per-field accuracy (of 30): task 25, scope 28, targets 29, day_filter 28, move 28, max_changes 28, protected 28, locked_days 29, keep_days 27, keep_time 29, keep_room 29, time window 22, min_break 26, day_to_empty 30, slot_search 25, date kind 27, duration_change 26, delivery 30, unsupported codes 26, needs_clarification 27, date_note 28.

Silent guesses in practice: H12 and H23 missed DURATION_CHANGE but were still flagged DATED_CHANGE, so they cannot run; H09 missed EXTRA_SESSION and would run the read-only finder without saying booking is unsupported. No case would have changed the timetable silently. Weakest field: time windows (22/30), e.g. "not before 9" read as a free block. Dev set for comparison: 18/40 strict, 0 silent guesses.
