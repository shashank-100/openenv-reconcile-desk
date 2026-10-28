---
license: other
license_name: mit-bsd-and-ogl-attributed
license_link: https://github.com/shashank-100/openenv-reconcile-desk/blob/main/ATTRIBUTION.md
pretty_name: Reconcile Desk
tags:
- rl-environment
- openenv
- terminal
- real-world-data
---
# Reconcile Desk

An attributed adaptation of jjmachan / vibrantlabsai Pool Desk v5's supplier-spending exercise, pinned at c5ea7ae8510fe2f01ee9c3154f6f6af0317bdead. The four GOV.UK input files are preserved with original provenance and SHA-256 hashes. Contains public sector information licensed under Open Government Licence v3.0. OpenEnv terminal models are BSD-3-Clause; our new implementation is MIT. Original source attribution and license notices are retained.

Five tasks teach an AI to inspect messy payment files, match supplier aliases, resolve revisions, remove duplicate exports, exclude cancellations and deliver an exact results CSV. The source-spend baseline uses three real government formats and cp1252 encodings. Four additions produce synthetic ledgers from those amounts with seeded record IDs, amount perturbations, shuffling, duplicate exports, revisions and cancellations. Synthetic records are training data, not factual claims about government payments.

Actions: exec, write_file, check, evaluate and finish, using the standard OpenEnv Tbench2Action schema. Each episode has a private workspace and unprivileged UID. The image requires no credentials or network downloads. OpenEnv is pinned to 86a180ede21e044f7929b9a7783ad83aa67d83a3.

Reward is binary: 1 only for correct supplier order, exact required columns, two-decimal finite monetary values and every department/combined total. Otherwise the final reward is 0. check returns bounded feedback with reward zero; evaluate terminates; the 32nd action automatically grades. finish terminates with zero.

The protected verifier never imports or executes the agent's Python code. Tests include an independent file-based reference solver, empty/incorrect/NaN output controls, symlink/FIFO rejection and session-isolation checks. Verification results are recorded in the public repository. No policy calibration, training improvement or Arena score is claimed. We have not reproduced the upstream 39-task environment, runtime or measured performance.

Source, task generator, input data, provenance and license notices: https://github.com/shashank-100/openenv-reconcile-desk

Upstream: https://huggingface.co/datasets/vibrantlabsai/pool-desk-v5/tree/c5ea7ae8510fe2f01ee9c3154f6f6af0317bdead

Task manifest: tasks.jsonl. A source archive and prepared submission request will be published in the source repository. Arena submission remains subject to explicit human review and approval.
