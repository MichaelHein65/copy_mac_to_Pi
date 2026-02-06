from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config.json"

DEFAULT_CONFIG = {
    "ssh_host": "pi5",
    "ssh_port": 22,
    "remote_base": "/mnt/Platte",
}


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = DEFAULT_CONFIG.copy()
    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    return data


app = Flask(__name__)


@app.get("/")
def index():
    cfg = load_config()
    return render_template("index.html", config=cfg)


@app.get("/api/remote/list")
def remote_list():
    cfg = load_config()
    path = request.args.get("path", "").strip() or cfg["remote_base"]
    host = cfg["ssh_host"]
    port = str(cfg["ssh_port"])

    print(f"[remote_list] path={path}")

    remote_cmd = (
        "bash -lc 'set -e; "
        f"cd -- {quote_shell(path)}; "
        "pwd; ls -a -p'"
    )
    cmd = ["ssh", "-p", port, host, remote_cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        print(f"[remote_list] error: {err or out or 'ssh failed'}")
        return jsonify({"ok": False, "error": err or out or "ssh failed"}), 400

    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return jsonify({"ok": False, "error": "invalid response"}), 400
    resolved = lines[0]
    items = []
    for line in lines[1:]:
        if line in (".", ".."):
            continue
        is_dir = line.endswith("/")
        items.append({"name": line.rstrip("/"), "type": "dir" if is_dir else "file"})

    return jsonify({"ok": True, "path": path, "resolved": resolved, "items": items})


@app.post("/api/upload")
def upload():
    cfg = load_config()
    host = cfg["ssh_host"]
    port = str(cfg["ssh_port"])
    remote_path = request.form.get("remote_path", "").strip()

    if not remote_path:
        return jsonify({"ok": False, "error": "remote_path is required"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"ok": False, "error": "no files"}), 400

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Save uploads to temp dir
        for f in files:
            name = Path(f.filename).name
            dest = tmpdir_path / name
            f.save(dest)

        # Use rsync for robust transfer
        rsync_cmd = [
            "rsync",
            "-a",
            "--progress",
            "-e",
            f"ssh -p {port}",
            f"{tmpdir}/",
            f"{host}:{remote_path.rstrip('/')}/",
        ]
        try:
            out = subprocess.check_output(rsync_cmd, stderr=subprocess.STDOUT, text=True)
            results.append({"ok": True, "output": out.strip()})
        except subprocess.CalledProcessError as e:
            return jsonify({"ok": False, "error": e.output.strip() or str(e)}), 400

    return jsonify({"ok": True, "results": results})


@app.post("/api/mkdir")
def mkdir():
    cfg = load_config()
    host = cfg["ssh_host"]
    port = str(cfg["ssh_port"])
    path = request.json.get("path", "").strip() if request.is_json else ""
    if not path:
        return jsonify({"ok": False, "error": "path is required"}), 400

    cmd = [
        "ssh",
        "-p",
        str(port),
        host,
        "bash",
        "-lc",
        f"mkdir -p -- {quote_shell(path)}",
    ]
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"ok": False, "error": e.output.strip() or str(e)}), 400

    return jsonify({"ok": True})


@app.post("/api/config")
def save_config():
    if not request.is_json:
        return jsonify({"ok": False, "error": "json required"}), 400
    data = request.json
    cfg = load_config()
    cfg.update(
        {
            "ssh_host": str(data.get("ssh_host", cfg["ssh_host"])).strip(),
            "ssh_port": int(data.get("ssh_port", cfg["ssh_port"])),
            "remote_base": str(data.get("remote_base", cfg["remote_base"])).strip(),
        }
    )
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return jsonify({"ok": True, "config": cfg})


def quote_shell(value: str) -> str:
    # Safe single-quote escaping for bash -lc
    return "'" + value.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=True)
