"""Local client-advisor workbench for generating messages from new inputs."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlsplit
import uuid
import webbrowser

from .generate import validate_output
from .prompt_loader import INPUT_FIELDS, LOCAL_ROOT, LOCAL_RUNS, PROJECT_ROOT, PROMPT_VERSION, ROOT, SUBMISSION, assemble

APP_ID = "veran-advisor-demo"
GENERATION_LOCK = threading.Lock()
WEB_ROOT = Path(__file__).with_name("web")
REPORT_ROOT = SUBMISSION


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        logging.info(fmt, *args)

    def respond(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path, content_type):
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/api/health":
            self.respond(200, {"app": APP_ID, "prompt_version": PROMPT_VERSION})
        elif path in ("/", "/index.html"):
            self.send_file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
        elif path in ("/report/report.html", "/report/BDE_Methodology_Evaluation_Improvements.pdf"):
            self.send_response(303)
            self.send_header("Location", "/report/B_Methodology.pdf")
            self.end_headers()
        elif path.startswith("/report/"):
            candidate = (REPORT_ROOT / (path[len("/report/"):] or "report.html")).resolve()
            if not candidate.is_relative_to(REPORT_ROOT.resolve()):
                self.send_error(403)
                return
            types = {".pdf": "application/pdf", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".json": "application/json; charset=utf-8", ".png": "image/png"}
            self.send_file(candidate, types.get(candidate.suffix, "application/octet-stream"))
        else:
            self.send_error(404)

    def do_POST(self):
        path = urlsplit(self.path).path
        expected_origins = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        if origin and origin not in expected_origins:
            self.respond(403, {"error": "请从本地工具页面操作。"})
            return
        if path == "/api/stop":
            if GENERATION_LOCK.locked():
                self.respond(409, {"error": "生成中，请稍后关闭。"})
                return
            self.respond(200, {"stopped": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if path != "/api/generate":
            self.send_error(404)
            return
        if self.headers.get_content_type() != "application/json":
            self.respond(415, {"error": "请使用页面表单提交。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("输入过长或为空。")
            supplied = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(supplied, dict):
                raise ValueError("案例输入格式不正确。")
            case = {key: supplied[key] for key in INPUT_FIELDS if key in supplied}
            case["case_id"] = "LIVE-" + uuid.uuid4().hex[:12]
            assemble(case)  # Validate the scenario before launching any model call.
        except (ValueError, UnicodeDecodeError) as exc:
            self.respond(400, {"error": str(exc)})
            return
        if not GENERATION_LOCK.acquire(blocking=False):
            self.respond(409, {"error": "正在生成上一组话术，请稍等。"})
            return
        started = time.monotonic()
        try:
            inputs = LOCAL_ROOT / "new_cases"
            inputs.mkdir(parents=True, exist_ok=True)
            case_path = inputs / (case["case_id"] + ".json")
            case_path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
            executable = Path(sys.executable)
            # pythonw has no console streams; use python.exe for captured subprocess output.
            if executable.name.lower() == "pythonw.exe":
                executable = executable.with_name("python.exe")
            result = subprocess.run([str(executable), "-m", "veran_advisor.generate", str(case_path)], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace", timeout=210, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if result.returncode:
                logging.error("Generation failed for %s: %s", case["case_id"], result.stderr)
                raise RuntimeError("生成未成功。请确认本机 Codex 已登录且网络可用，再重试。")
            output = json.loads(result.stdout)
            validate_output(output)
            metadata = None
            for meta_path in sorted(LOCAL_RUNS.glob("*/metadata.json"), reverse=True):
                try:
                    candidate = json.loads(meta_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if candidate.get("case_id") == case["case_id"]:
                    metadata = candidate
                    break
            if metadata is None or metadata.get("run_status") != "completed":
                raise RuntimeError("运行记录未完整保存，请重试。")
            self.respond(200, {**output, "run_id": metadata["run_id"], "case_id": case["case_id"], "prompt_version": metadata["prompt_version"], "model": metadata.get("reported_model"), "elapsed_seconds": round(time.monotonic() - started, 1)})
        except subprocess.TimeoutExpired:
            self.respond(504, {"error": "生成超时，请检查网络后重试。"})
        except Exception as exc:
            logging.exception("Live generation failed")
            self.respond(500, {"error": str(exc) if isinstance(exc, RuntimeError) else "生成未成功，详细信息已保存在本地运行日志。"})
        finally:
            GENERATION_LOCK.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    LOCAL_ROOT.mkdir(exist_ok=True)
    logging.basicConfig(filename=LOCAL_ROOT / "tool.log", level=logging.INFO, encoding="utf-8")
    url = f"http://127.0.0.1:{args.port}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        # A second double-click should reopen the running demo, not start a duplicate.
        from urllib.request import urlopen
        try:
            with urlopen(url + "api/health", timeout=2) as response:
                existing = json.load(response)
            if existing.get("app") != APP_ID:
                raise RuntimeError("Port belongs to another application")
        except Exception as exc:
            raise RuntimeError("工具端口被占用，请使用 --port 指定其他端口。") from exc
        if not args.no_browser:
            webbrowser.open(url)
        return
    logging.info("Demo listening at %s", url)
    if sys.stdout is not None:
        print(f"VERAN live demo: {url}", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
