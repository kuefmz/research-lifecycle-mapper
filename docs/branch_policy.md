# Branch selection and immutable inputs

Policy identifier: main-then-master-v1.

For every live acquisition, first request the actual branch named main. Only if that branch is not found, try the actual branch named master. Do not use repository default HEAD, other branches, tags, releases, or caller-supplied commits as substitutes. API authentication/rate/network failures do not trigger branch substitution. A repository inaccessible at both branch endpoints is recorded as unavailable, not as six negative stages.

Resolve the selected branch once to its immutable commit and analyze that commit's tree and blobs. Retain selected_branch, branch_policy, commit and content hashes in every snapshot and corpus result. The Git transport inventories exact remote heads and verifies refs/remotes/origin/main or refs/remotes/origin/master, so a same-named tag cannot substitute. Read-only historical replay remains available with its original provenance.

This policy standardizes the integration snapshot used by this study while accommodating older repositories. The reproducibility practice is to pin and preserve the resolved commit, configuration, rules and input data. A branch name alone does not establish that it contains final research outputs. Some projects use release tags or other branches for publications; those are outside this policy and must be discussed as a limitation. Report main/master counts, inaccessible repositories, failures and complete evaluated N separately.

Do not combine historical default-branch measurements with new-policy results without identifying the different input revisions and cohorts. The human annotation-time revisions may differ from newly acquired commits.
