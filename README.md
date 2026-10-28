# Reconcile Desk

Teach an AI to reconcile messy supplier-payment files and deliver a correct CSV.

Adapted with attribution from jjmachan / vibrantlabsai Pool Desk v5's public supplier-spending task. This version reuses the pinned government input data and OpenEnv's BSD terminal data models. It adds an independent runnable server and verifier plus four synthetic tasks. See ATTRIBUTION.md and upstream/manifest.json.

| Task | Work the model practices |
|---|---|
| source-spend | Match supplier aliases and reconcile three real department CSV formats and encodings. |
| revised-payments | Apply the newest payment revision rather than summing obsolete records. |
| duplicate-exports | Count duplicate exports once while keeping distinct payments. |
| cancelled-payments | Exclude payments cancelled in their latest revision. |
| mixed-reconciliation | Combine revision, duplicate and cancellation rules. |

The baseline uses the preserved public data. Other tasks derive synthetic ledgers from those payments, with seeded amount perturbations, record IDs, shuffling and corrections. All selection rules are visible to the agent. Reward is binary: exactly correct supplier order, formatting and all four monetary columns earn 1; other final outputs earn 0. `check` provides feedback with reward 0, `evaluate` finishes, and the 32nd action automatically grades. `finish` terminates with zero. No policy calibration or private-task improvement is claimed.

Actions use the standard OpenEnv Tbench2Action schema: action_type (`exec`, `write_file`, `check`, `evaluate`, `finish`), command, file_path and content. Files live in the reset observation's task_path; commands start there. Read instruction.txt first. Paths for write_file must be relative. Python standard library is available; no pip install or external service is needed.

Agent commands are refused outside the Docker image. Inside the image, each session gets a private directory and distinct unprivileged Linux UID. The server/grader run separately as root with /app inaccessible to agent UIDs. Commands have a 15-second wall timeout, 12-second CPU limit, 768 MiB address-space limit, no-new-privileges, bounded output, process/file limits, and UID process cleanup. This is defense in depth within the Arena's container sandbox, not an independent hostile multi-tenant security boundary. No credentials are embedded. Grading reads data only and never imports or executes submitted code.

Build from this directory:

```
DOCKER_DEFAULT_PLATFORM=linux/amd64 openenv build --context . --dockerfile Dockerfile -t reconcile-desk:dev
```

Then run on port 8000 and use `openenv validate --url http://localhost:8000`. Unit and native replay scripts are in tests/. A deployment or Arena submission must be reviewed separately. This candidate does not change or submit the earlier Compiler Register Lab.
