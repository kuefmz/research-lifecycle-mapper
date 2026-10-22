# Minimal local UI

```bash
uv sync --frozen
uv run --frozen python -m lifecycle_mapper ui
```

Open http://127.0.0.1:8000. Enter an HTTPS root GitHub repository URL. The UI shows all six
stages for documentation, code and combined, the resolved commit, and full inspectable
JSON evidence with a download link. Only one repository runs at a time.

The implementation is `src/lifecycle_mapper/demo.py`. It launches the same corpus runner
as the paper, with one worker, all modes, 10 MiB per file, the packaged final catalog,
main/master policy and the 120-second per-repository guard. Without GITHUB_TOKEN it uses
Git acquisition; with a token it uses hybrid. Missing Git, network failures, inaccessible
repositories and absent allowed branches remain failures rather than fabricated zeros.

Optional Bash token setup, before starting the UI:

```bash
read -rsp 'GitHub token: ' GITHUB_TOKEN
echo
export GITHUB_TOKEN
uv run --frozen python -m lifecycle_mapper ui --port 8001 --state-dir local/demo
```

Use the printed loopback URL. Tokens are not accepted through the browser or stored in
results. Jobs and progress.log live under the state directory. Completed JSON can be
inspected offline; current UI job history itself is in memory and resets on restart.
The server is a local demonstration, not a production multiuser deployment. Repository
source is inspected without executing it.

The older `web.py`/`ui/index.html` remain compatibility components for historical UI
exports and regression tests; the advertised `ui` command uses the minimal demo instead.
