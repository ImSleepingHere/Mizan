# Request interpreter evaluation (spec §18.2, §18.7)

- `handwritten_test.jsonl`: 30 real professor requests with expected interpretations, approved and **frozen on 2026-09-27** (SHA-256 `74f827453cdfff631fc0942aa106fc73c3a0de8e34fdd17889a384158c1ae868`, checked by `tests/test_interpreter.py` and the eval script). Never used for training or prompt work. Scored **once**, at the end of items 1–4.
- `dev_set.py` → `dev.jsonl`: 40 development cases written by Claude in its own wording. Prompt and rule work uses only this set.
- `scoring.py`: strict exact match (headline), per-field accuracy, silent guesses (an expected unsupported code missing) and false flags, split by Arabic / English / mixed.
- `eval_interpreter.py --set dev` or `--set test --final` (needs the local model on port 11435). The test run refuses to run twice or on a modified file.

Test context: `requester_role` professor, own sections S087–S091, today 2026-09-27 (Sunday). Rules: finding a slot is in scope whatever the date wording (`date_note` when a date is mentioned); booking on a date is EXTRA_SESSION or DATED_CHANGE.

Caveat: the prompt author also wrote the test expectations, so the test set is not blind to the author; it is blind to prompt iteration.
