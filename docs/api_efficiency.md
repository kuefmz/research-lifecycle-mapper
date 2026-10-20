# API acquisition efficiency and quota waiting

Hybrid acquisition normally requests one main branch object and one recursive
Git tree per repository (three requests when master fallback is needed), with
eligible files fetched from commit-pinned raw URLs. No bearer token is sent to
raw URLs. Actual counts can be much higher for large truncated trees, retries,
or API blob transport. Inspect manifest.json's configuration.transport before
attributing a high count. This implementation cannot diagnose an old run from
its aggregate summary alone.

Truncated-tree recovery now requests recursive subtrees instead of one request
per directory; only still-truncated subtrees require further splitting. Repeated
tree SHAs are cached within that inventory. This preserves a complete inventory,
file eligibility and classifier rules, rather than dropping paths to save calls.
Small nontruncated repositories still require the normal two/three metadata calls.
Tests verify paths and request reduction on repeated/deep subtree fixtures; live
savings depend on the actual tree shapes and are not yet measured.

The corpus REST gate serializes requests, including retries. Successful responses
with X-RateLimit-Remaining=0 schedule a shared wait until X-RateLimit-Reset plus a
two-second margin. Primary reset responses continue waiting/retrying across
quota windows; they are not abandoned after five waits. Retry-After is honored,
and secondary limits without a primary reset use bounded exponential backoff.
Recognized secondary-limit 403 bodies are classified but never persisted.
Unrelated permission failures are not classified as quota exhaustion. Long waits
are broken into at most 60-second sleeps and logged. Waiting renews a quota window;
it does not repair an expired/revoked token (401 stops the run).

Result api_calls counts actual REST attempts including internal HTTP retries.
The aggregate api_calls field includes counts from saved checkpoints on resumes;
it is not token consumption during the latest session. New summary fields:

- session_api_network_calls: actual REST requests during this invocation.
- rate_limit_wait_seconds: time slept in the shared gate for quota cooldowns.

No /rate_limit polling is needed. Raw-file service limits remain separate and
can still cause partial scans; size, decoding and unsupported artifacts can also
cause incomplete scans. Do not infer the cause of 37 partial results from the
aggregate alone. Keep a single live API runner per token/session; independent
processes do not share the gate.

After an active run completes, update the code and start a NEW output directory
for a new acquisition. Implementation hashes deliberately prevent mixing old and
new acquisition code in one resumed scientific run. Existing completed runs can
be exported/evaluated offline with the commands below; no new GitHub requests or
reacquisition are needed.

```bash
uv run --frozen python -m lifecycle_mapper.corpus export \
  --output data/runs/benchmark-main-master \
  --reference data/research_lifecycle_benchmark_100_msr27.xlsx
uv run --frozen python -m lifecycle_mapper.summarize \
  --run data/runs/benchmark-main-master --expected-repositories 100
cat data/runs/benchmark-main-master/documentation_metrics.json
```

XLSX reference loading explicitly reads final_agreement. The primary analysis is
documentation-only, matching annotation scope; the summarizer uses repositories
with complete documentation scans and all six labels. All-mode complete=63 is
not necessarily documentation evaluated N; inspect reported coverage. Other
modes/evidence remain separate outputs, not replacements for documentation labels.

GitHub rate-limit guidance:
https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
