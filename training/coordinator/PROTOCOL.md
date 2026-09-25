# Coordinator experiment protocol — frozen before training

- Base: official Qwen/Qwen3-8B at the revision in model_manifest.json. No training of other agent roles.
- Method: 4-bit NF4 base, attention-only LoRA rank 8, alpha 16, dropout 0.05. Frozen base weights; assistant-completion loss only. Two epochs, 480 examples, accumulation 8, AdamW maximum learning rate 0.0001. Seed 4101.
- Dataset: synthetic coordinator states, not institutional data or independently expert-labeled cases. 480 train, 60 validation, 120 test; balanced English/Arabic. IDs, numerical values and request phrase banks differ by split. Test field ordering and source-injection wording are held out. The shared state generator means this measures generalization within the implemented workflow, not broad real-world intelligence.
- Selection: select only by validation loss after epoch 1 or 2. No hyperparameter/prompt changes based on test results. File hashes recorded before training.
- Primary comparison: same official base loaded with NF4, same inference settings and prompts, with versus without the selected adapter. Greedy decoding, 128 output-token cap, no grammar restriction. Report valid bounded JSON, next-action correctness, conclusion disposition, combined pass, and premature finalization.
- Multiple reasonable next specialists receive credit. Completed reviews must not be repeated, impact needs a candidate, rejected or stale reviews need corrective routing. The explicit maximum change limit is authoritative.
- Secondary control: existing deployment GGUF baseline on the same test, reported separately because quantization/runtime differ. Production's constrained schemas can mask model mistakes and remain required irrespective of the training outcome.
- Report paired differences and uncertainty. A gain on this small synthetic benchmark does not prove deployment improvement or justify removing checks. Training loss alone is not success.
- Approval: adapter stays outside the live application until the user explicitly approves it. Existing inference is paused only to free GPU memory and restored after the experiment.
