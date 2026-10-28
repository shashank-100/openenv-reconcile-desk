# Attribution and scope of reuse

This candidate adapts the supplier-spending exercise curated by jjmachan / vibrantlabsai in Pool Desk v5:
https://huggingface.co/datasets/vibrantlabsai/pool-desk-v5/tree/c5ea7ae8510fe2f01ee9c3154f6f6af0317bdead
Task: tasks/office-white-collar/b1-uk-supplier-spend-02.

The four input files are preserved byte-for-byte in upstream/data, with immutable upstream paths and SHA-256 hashes in upstream/manifest.json. Original provenance and the dataset's per-task license table are preserved. Contains public sector information licensed under the Open Government Licence v3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ . The original data publishers are DWP, DBT and Defra. No endorsement by these departments or by vibrantlabsai is implied.

The baseline's matching rule, expected output shape and task concept derive from the attributed Pool Desk task. The instructions, generator, terminal runtime, reference solver and strict verifier here are new implementations. The upstream verifier, solution script and unavailable pool base image are not redistributed or claimed as ours. The original 39-task environment and its performance have not been reproduced.

server/models.py is copied unmodified from Meta PyTorch OpenEnv envs/tbench2_env/models.py at 86a180ede21e044f7929b9a7783ad83aa67d83a3, under BSD-3-Clause. Its copyright header remains and upstream/OpenEnv-LICENSE contains its license. OpenEnv itself is installed at that same revision.

Our additions are synthetic revisions, export duplicates, cancellation events, per-episode amount perturbations and record IDs. These synthetic records are training exercises and are not additional factual claims about the government payments. New code is under MIT (LICENSE); this does not relicense upstream material.
