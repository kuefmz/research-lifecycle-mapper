# Acquisition and API usage

The maintained corpus runner supports hybrid (raw content plus REST metadata/tree), API,
and Git transports. Paper commands use hybrid with one worker and pacing. Raw-content
requests do not consume REST quota but still incur network time and service constraints.
The token is read from GITHUB_TOKEN; do not place it in files, browser input or command
arguments. Git transport can acquire public repositories without this token.

Rate-limit handling waits according to the observed response/reset where possible. The
120-second repository deadline includes waits, so a quota-starved repository can time out
before reset rather than wait indefinitely. Retry after reset using a compatible checkout
and the runner's retry options; retain failure diagnostics and original attempts.

Summary API calls are observed REST calls, not total HTTP requests. Session timing after
resume is not fresh end-to-end throughput. Both limits and timing provenance belong in
result documentation. See method.md and results.md.
