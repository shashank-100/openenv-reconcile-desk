# Verification

Unit tests independently reconstruct every task's expected totals over five seeds, compare selected baseline totals with the original published numerical facts, verify pinned input hashes and reject empty, altered, reordered, non-finite and unsafe output files. Shortcut tests sum every exported row and must fail each synthetic task.

The reference solver is authored independently of the protected generator and operates only on the files and public instructions. It is not included in the production image. Native replay writes it using agent actions, executes it under the actual unprivileged session UID and checks rewards over the network.

Run unit tests using a Python environment with the pinned OpenEnv and pytest installed. Run replay.py against a running production container with websockets installed. Test artifacts placed inside a verification container must be root-only, so the unprivileged agent cannot read the test/reference solution directory.
