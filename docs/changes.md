# What is reused, and what we added

## Reused

- The original four supplier-spending input files, pinned to Pool Desk v5 c5ea7ae8510fe2f01ee9c3154f6f6af0317bdead and checked with SHA-256.
- The task concept, supplier normalization rule and result column shape, with attribution.
- OpenEnv's BSD-licensed terminal action/observation/state model code at the exact Arena SDK commit.

## Added

- A runnable single-image server with five task IDs.
- Four synthetic ledger variants: revisions, duplicate exports, cancellations and a combined task.
- Seeded record IDs, amount perturbations and row order; outputs change across seeds.
- Exact decimal grading rejecting NaN, infinity, duplicate/missing supplier rows, wrong order and one-penny errors.
- Protected data-only grading, safe output-file reads and separate session UIDs.
- Independent reference solver, incorrect/shortcut controls and native protocol tests.

The upstream runtime, base-image hardening, model calibration and 39-task collection have not been reproduced. Neither the upstream leaderboard score nor its measurement solve rates apply to this adaptation. No model calls, paid training or Arena submission are authorized by these tests. The candidate remains review-only until the human approves the exact submission request.
