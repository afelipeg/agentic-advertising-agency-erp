# Evaluation contract

Define acceptance cases before changing skill instructions. `scenarios.json` is a synthetic behavioral suite, not proof of model performance. Keep expected answers outside installed skill folders. Use independent holdout cases for model comparisons.

Run `npm run eval` for deterministic business-rule cases. Run `python3 scripts/evaluate_trajectory.py trajectory.json` to grade an exported agent trajectory against a scenario. The trajectory evaluator checks observable event evidence, not hidden reasoning. Host adapters must export the documented event format; an assertion that an event happened is not a provider execution receipt.

For each skill/model/client combination, execute scenarios against isolated fixtures, save sanitized tool/model events, inspect artifacts and resulting business state, then score outcome correctness, authorization compliance, evidence, recovery, task cost and active latency. A model judge may assist with narrative quality; critical business and permission checks require deterministic assertions or reviewer adjudication. Repeat stochastic cases; report sample size, confidence intervals and failure categories.

Block release on any critical safety failure or a regression beyond the versioned baseline tolerance. Keep task-level results separated by domain; an average must not hide a failed payment or tenant boundary. Do not manufacture baseline scores when no model runs were performed.

Promote models using shadow runs first, then a small assigned cohort whose users/actions retain the same approval gates. Compare successful-task cost including tool fees, retries, fallback, review and rework. Fine-tune only from reviewed, rights-cleared, de-identified examples; preserve a separate holdout. Real failures can be added only after removing secrets/PII and obtaining the appropriate reuse authorization.
