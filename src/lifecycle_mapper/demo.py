"""Small loopback-only UI that delegates to the paper's guarded corpus runner."""

import json
import os
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from .acquisition import repository_id

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Research Lifecycle Mapper</title><style>
body{font:16px system-ui;max-width:900px;margin:3rem auto;padding:1rem;background:#fafafa;color:#17202a}
input{width:65%;padding:.7rem}button{padding:.7rem;cursor:pointer}pre{white-space:pre-wrap}
table{border-collapse:collapse;width:100%;margin:1rem 0}td,th{text-align:left;border-bottom:1px solid #ccc;padding:.6rem}
</style><h1>Research Lifecycle Mapper</h1>
<p>Detect evidence in a public GitHub repository. Main, otherwise master; 120-second repository deadline; 10 MiB per file.</p>
<form id="form"><label for="url">GitHub repository URL</label><p><input id="url" type="url" placeholder="https://github.com/owner/repository" required> <button id="run">Analyze</button></p></form>
<p id="status" role="status"></p><div id="result"></div>
<p>1: evidence detected · 0: no evidence detected in a complete scan · ?: incomplete scan. These findings do not establish reproducibility.</p>
<script>
const status=document.querySelector('#status'),result=document.querySelector('#result'),button=document.querySelector('#run');
function text(tag,value,parent){const el=document.createElement(tag);el.textContent=value;parent.append(el);return el;}
function show(data){result.replaceChildren();if(data.error)text('p',data.error,result);
text('p','Repository: '+data.requested_url+' | Commit: '+(data.commit||'unavailable'),result);
const table=document.createElement('table');result.append(table);const head=document.createElement('tr');table.append(head);
['Mode','Collection','Processing','Method','Experimentation','Evaluation','Dissemination'].forEach(v=>text('th',v,head));
for(const mode of data.modes||[]){const row=document.createElement('tr');table.append(row);text('td',mode.mode,row);
for(const stage of ['Collection','Processing','Method','Experimentation','Evaluation','Dissemination'])text('td',mode.predictions[stage]??'?',row);}
const details=document.createElement('details');result.append(details);text('summary','Evidence and full result',details);text('pre',JSON.stringify(data,null,2),details);
const link=document.createElement('a');link.textContent='Download result JSON';link.download='lifecycle-result.json';link.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));result.append(link);}
document.querySelector('#form').onsubmit=async e=>{e.preventDefault();button.disabled=true;result.replaceChildren();status.textContent='Starting…';try{
const response=await fetch('/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:document.querySelector('#url').value})});
const job=await response.json();if(!response.ok)throw Error(job.error);
const poll=async()=>{try{const r=await fetch('/jobs/'+job.id);const data=await r.json();status.textContent=data.status;
if(data.status==='running'){setTimeout(poll,1000);return;}button.disabled=false;if(data.result)show(data.result);else text('pre',data.error||'No result',result);
}catch(error){status.textContent=error.message;button.disabled=false;}};poll();
}catch(error){status.textContent=error.message;button.disabled=false;}};
</script></html>"""


class Demo:
    def __init__(self, state: Path):
        self.state = state.resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def start(self, url: str) -> str:
        normalized = "https://github.com/" + repository_id(url.strip().rstrip("/"))
        with self.lock:
            if any(job["status"] == "running" for job in self.jobs.values()):
                raise ValueError("A repository is already being analyzed; please wait")
            identifier = uuid.uuid4().hex
            self.jobs[identifier] = {"status": "running"}
        directory = self.state / identifier
        directory.mkdir()
        input_path = directory / "input.txt"
        input_path.write_text(normalized + "\n", encoding="utf-8")

        def execute() -> None:
            try:
                output = directory / "run"
                command = [
                    sys.executable,
                    "-m",
                    "lifecycle_mapper.corpus",
                    "run",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output),
                    "--expected-repositories",
                    "1",
                    "--workers",
                    "1",
                    "--mode",
                    "all",
                    "--transport",
                    "hybrid" if os.environ.get("GITHUB_TOKEN") else "git",
                    "--max-bytes",
                    "10485760",
                ]
                with (directory / "progress.log").open("w", encoding="utf-8") as log:
                    process = subprocess.run(command, stdout=log, stderr=log, timeout=150)
                if process.returncode:
                    raise ValueError("Analysis could not finish; inspect the local progress.log")
                paths = list((output / "repositories").glob("*/result.json"))
                if len(paths) != 1:
                    raise ValueError("Expected one saved result")
                value = {"status": "finished", "result": json.loads(paths[0].read_bytes())}
            except Exception as error:
                value = {"status": "failed", "error": str(error)}
            with self.lock:
                self.jobs[identifier] = value

        threading.Thread(target=execute, daemon=True).start()
        return identifier


def make_server(app: Demo, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def respond(self, value: Any, status: int = 200) -> None:
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(PAGE.encode())
            elif self.path.startswith("/jobs/"):
                with app.lock:
                    job = app.jobs.get(self.path.removeprefix("/jobs/"))
                self.respond(job or {"error": "Unknown job"}, 200 if job else 404)
            else:
                self.respond({"error": "Not found"}, 404)

        def do_POST(self) -> None:
            if self.path != "/jobs":
                self.respond({"error": "Not found"}, 404)
                return
            # Only same-origin browser submissions may start local work.
            origin = self.headers.get("Origin")
            if (
                origin
                and origin
                != f"http://127.0.0.1:{cast(ThreadingHTTPServer, self.server).server_port}"
            ):
                self.respond({"error": "Unexpected origin"}, 403)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096:
                    raise ValueError("Invalid request size")
                request = json.loads(self.rfile.read(size))
                self.respond({"id": app.start(request["url"])}, 202)
            except (ValueError, KeyError, TypeError) as error:
                self.respond({"error": str(error)}, 400)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(root: Path, state_dir: Path, port: int = 8000) -> None:
    server = make_server(Demo(state_dir), port)
    print(f"Open http://127.0.0.1:{server.server_port} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
