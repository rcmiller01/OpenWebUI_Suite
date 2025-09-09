#!/usr/bin/env python3
"""
Unified builder/deployer for the OpenWebUI+OpenRouter stack.

Usage examples:
  # Full run: update → deps → config → tests → build base & services → deploy → integration → sanity
  python scripts/build_all.py --all --tag prod-2025-09 --push --multi-arch

  # Only build images (your original flow), local arch only:
  python scripts/build_all.py --build --tag dev

  # Just config + deploy (no rebuild):
  python scripts/build_all.py --config --deploy

Flags affecting integration test behavior:
  --ignore-test-fail   # do NOT fail the script if integration test returns non-zero
"""

from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Project constants
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(__file__).resolve().parent.parent
ENV_FILE     = REPO_ROOT / ".env"
CONFIG_DIR   = REPO_ROOT / "config"
PRESETS_FILE = CONFIG_DIR / "presets.json"
TOOLS_FILE   = CONFIG_DIR / "tools.json"

# Your original service build order (kept verbatim)
SERVICES = [
    "00-pipelines-gateway",
    "01-intent-router",
    "02-memory-2.0",
    "03-feeling-engine",
    "04-hidden-multi-expert-merger",
    "05-drive-state",
    "06-byof-tool-hub",
    "07-tandoor-sidecar",
    "08-openbb-sidecar",
    "09-proactive-daemon",
    "10-multimodal-router",
    "11-stt-tts-gateway",
    "13-policy-guardrails",
    "14-telemetry-cache",
    "15-bytebot-gateway",
    "16-fastvlm-sidecar",
]

# Env sanity
REQUIRED_ENVS = [
    "OPENROUTER_API_KEY",
    "OPENROUTER_ENABLED",
]
OPTIONAL_ENVS = [
    "LOCAL_FALLBACK_ENABLED",
    "N8N_WEBHOOK_URL",
    "N8N_SHARED_HEADER",
    "N8N_SHARED_SECRET",
    "MCP_ENDPOINT",
    # Integration test can rely on this if your test script reads it,
    # but the test_openrouter_complete.py already hardcodes the Memory URL.
    "MEMORY_SERVICE_URL",
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def run(cmd: str|list[str], dry=False, check=True, cwd: Path|None=None):
    if isinstance(cmd, list):
        printable = " ".join(cmd)
    else:
        printable = cmd
    print(f"\n→ {'(dry) ' if dry else ''}$ {printable}")
    if dry:
        return 0, "", ""
    proc = subprocess.run(cmd, shell=isinstance(cmd,str), cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"Command failed: {printable}")
    return proc.returncode, proc.stdout, proc.stderr

def backup_file(path: Path):
    if not path.exists():
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, bkp)
    print(f"• Backup: {path.name} → {bkp.name}")

def load_env():
    if ENV_FILE.exists():
        print(f"• Loading env: {ENV_FILE}")
        for line in ENV_FILE.read_text().splitlines():
            m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$', line)
            if not m:
                continue
            k, v = m.group(1), m.group(2)
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            os.environ.setdefault(k, v)

def check_envs():
    missing = [k for k in REQUIRED_ENVS if not os.environ.get(k)]
    if missing and os.environ.get("LOCAL_FALLBACK_ENABLED","").lower() not in ("1","true","yes","on"):
        print(f"‼ Missing required envs: {', '.join(missing)}")
        print("   Provide them in .env or set LOCAL_FALLBACK_ENABLED=true for offline-only.")
        raise SystemExit(2)
    for k in OPTIONAL_ENVS:
        if not os.environ.get(k):
            print(f"• Optional env not set: {k}")

def detect_pkg_managers():
    return ((REPO_ROOT / "requirements.txt").exists(),
            (REPO_ROOT / "pyproject.toml").exists(),
            (REPO_ROOT / "package.json").exists())

def git_update(dry=False):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    run("git rev-parse --is-inside-work-tree", dry=False)
    run(f"git add -A && git diff --quiet || git commit -m 'chore: pre-deploy {ts}' || true", dry=dry, check=False)
    run(f"git tag -f pre-deploy-{ts}", dry=dry, check=False)
    run("git fetch --all --prune", dry=dry)
    run("git pull --rebase", dry=dry)

def install_deps(dry=False):
    has_req, has_pyproject, has_package = detect_pkg_managers()
    py = shutil.which("python3") or sys.executable
    pip = f"{py} -m pip"
    if has_req or has_pyproject:
        run(f"{pip} install --upgrade pip", dry=dry, check=False)
    if has_req:
        run(f"{pip} install -r requirements.txt", dry=dry, check=False)
    elif has_pyproject:
        uv = shutil.which("uv")
        if uv:
            run(f"{uv} pip install -e .", dry=dry, check=False)
        else:
            run(f"{pip} install -e .", dry=dry, check=False)
    if has_package:
        if shutil.which("pnpm"):
            run("pnpm install --frozen-lockfile || pnpm install", dry=dry, check=False)
            run("pnpm build || true", dry=dry, check=False)
        elif shutil.which("yarn"):
            run("yarn install --frozen-lockfile || yarn install", dry=dry, check=False)
            run("yarn build || true", dry=dry, check=False)
        else:
            run("npm ci || npm install", dry=dry, check=False)
            run("npm run build || true", dry=dry, check=False)

def ensure_config_files(dry=False):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    desired_presets = [
        {"name":"Tool-DeepSeekV3","model":"deepseek/deepseek-chat","temperature":0.2,"top_p":0.9,"tools":True,"vision":False},
        {"name":"Vision-GLM4V","model":"zhipuai/glm-4v-9b","temperature":0.5,"top_p":0.9,"tools":False,"vision":True},
        {"name":"Venice-Uncensored","model":"venice/uncensored:free","temperature":0.85,"top_p":0.9,"tools":False,"vision":False},
        {"name":"Qwen3-Coder","model":"qwen/qwen3-coder","temperature":0.15,"top_p":0.9,"tools":False,"vision":False}
    ]
    if PRESETS_FILE.exists():
        backup_file(PRESETS_FILE)
        try:
            current = json.loads(PRESETS_FILE.read_text() or "[]")
            by_name = {p.get("name"):p for p in current if isinstance(p,dict) and p.get("name")}
            for p in desired_presets:
                by_name[p["name"]] = p
            PRESETS_FILE.write_text(json.dumps(list(by_name.values()), indent=2))
        except Exception as e:
            print(f"⚠ presets merge failed: {e}; writing defaults.")
            PRESETS_FILE.write_text(json.dumps(desired_presets, indent=2))
    else:
        PRESETS_FILE.write_text(json.dumps(desired_presets, indent=2))
    print(f"• ensured {PRESETS_FILE}")

    desired_tools = [
        {
            "name":"n8n_router",
            "description":"Dispatch an action to local n8n",
            "parameters":{
                "type":"object",
                "properties":{
                    "family":{"type":"string","enum":["proxmox","git","deploy","backup","image"]},
                    "action":{"type":"string"},
                    "payload":{"type":"object","additionalProperties":True}
                },
                "required":["family","action"]
            }
        },
        {
            "name":"mcp_call",
            "description":"Call an MCP tool exposed by the local MCP server",
            "parameters":{
                "type":"object",
                "properties":{
                    "tool":{"type":"string"},
                    "args":{"type":"object","additionalProperties":True}
                },
                "required":["tool"]
            }
        }
    ]
    if TOOLS_FILE.exists():
        backup_file(TOOLS_FILE)
        try:
            current = json.loads(TOOLS_FILE.read_text() or "[]")
            by_name = {t.get("name"):t for t in current if isinstance(t,dict) and t.get("name")}
            for t in desired_tools:
                by_name[t["name"]] = t
            TOOLS_FILE.write_text(json.dumps(list(by_name.values()), indent=2))
        except Exception as e:
            print(f"⚠ tools merge failed: {e}; writing defaults.")
            TOOLS_FILE.write_text(json.dumps(desired_tools, indent=2))
    else:
        TOOLS_FILE.write_text(json.dumps(desired_tools, indent=2))
    print(f"• ensured {TOOLS_FILE}")

def run_tests(dry=False):
    # Python
    if (REPO_ROOT / "pytest.ini").exists() or any((REPO_ROOT / "tests").glob("*.py")):
        py = shutil.which("python3") or sys.executable
        run(f"{py} -m pytest -q", dry=dry, check=False)
    # JS
    if (REPO_ROOT / "package.json").exists():
        run("npm test --silent || true", dry=dry, check=False)

def detect_runtime():
    # systemd?
    code, out, _ = run("systemctl list-unit-files | grep -i 'open.*webui' || true", dry=False, check=False)
    unit = None
    for line in out.splitlines():
        m = re.search(r'^(open[-]?webui\S*)\s', line.strip())
        if m:
            unit = m.group(1); break
    # docker compose?
    dc_file = None
    for name in ("docker-compose.yml", "compose.yml"):
        if (REPO_ROOT / name).exists():
            dc_file = REPO_ROOT / name; break
    return unit, dc_file

def deploy(dry=False, ignore_test_fail=False):
    unit, dc_file = detect_runtime()
    if unit:
        print(f"• systemd unit detected: {unit}")
        run("sudo systemctl daemon-reload", dry=dry, check=False)
        run(f"sudo systemctl restart {unit}", dry=dry, check=False)
        run(f"sudo systemctl status {unit} --no-pager -l | tail -n +1", dry=dry, check=False)
    elif dc_file:
        print(f"• docker compose detected: {dc_file.name}")
        run(f"docker compose -f {dc_file} up -d --build", dry=dry, check=False)
        run(f"docker compose -f {dc_file} ps", dry=dry, check=False)
        run(f"docker compose -f {dc_file} logs --no-color --tail=150", dry=dry, check=False)
    else:
        print("‼ No systemd unit or docker compose file found; skipping deploy.")

    # 🔥 New: integration test after services are up
    test_file = REPO_ROOT / "test_openrouter_complete.py"
    if test_file.exists():
        print("\n⏳ Running integration tests (including Memory service)…")
        py = shutil.which("python3") or sys.executable
        try:
            # Use check=True unless ignore_test_fail is set
            run(f"{py} {test_file}", dry=dry, check=not ignore_test_fail)
        except Exception as e:
            msg = f"⚠ Integration test failed: {e}"
            if ignore_test_fail:
                print(msg)
            else:
                raise
    else:
        print("ℹ Skipping integration test (test_openrouter_complete.py not found).")

def deploy_memory_service(remote_host="192.168.50.15", dry=False):
    """Deploy Memory 2.0 service to remote Docker host"""
    print(f"🧠 Deploying Memory 2.0 service to {remote_host}...")
    memory_dir = REPO_ROOT / "02-memory-2.0"
    if not memory_dir.exists():
        print(f"❌ Memory service directory not found: {memory_dir}")
        return False

    import tempfile, tarfile

    with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
        with tarfile.open(tmp.name, 'w:gz') as tar:
            tar.add(memory_dir, arcname='memory-service')

        scp_cmd = f"scp {tmp.name} root@{remote_host}:/tmp/memory-service.tar.gz"
        run(scp_cmd, dry=dry)

        deploy_script = r"""
            set -e
            cd /tmp
            tar -xzf memory-service.tar.gz
            cd memory-service
            docker build -t owui/memory-2.0:latest .
            docker stop memory-service 2>/dev/null || true
            docker rm memory-service 2>/dev/null || true
            docker run -d --name memory-service --restart unless-stopped \
                -p 8102:8102 owui/memory-2.0:latest
            sleep 5
            curl -f http://localhost:8102/healthz || (echo 'Health check failed' && exit 1)
        """
        ssh_cmd = f"ssh root@{remote_host} '{deploy_script}'"
        run(ssh_cmd, dry=dry)

        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    print(f"✅ Memory service deployed to http://{remote_host}:8102")
    return True

def sanity_checks(dry=False):
    # OpenRouter key presence (unless local fallback)
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("⚠ OPENROUTER_API_KEY not set; remote routing may fail.")
    # n8n reachability (optional)
    url = os.environ.get("N8N_WEBHOOK_URL")
    if url:
        hdr = os.environ.get("N8N_SHARED_HEADER", "X-N8N-Key")
        sec = os.environ.get("N8N_SHARED_SECRET", "")
        curl_cmd = (f"curl -s -o /dev/null -w '%{{http_code}}' "
                    f"-H '{hdr}: {sec}' '{url}' || true")
        run(curl_cmd, dry=dry, check=False)

    # Memory service health
    memory_url = os.environ.get("MEMORY_SERVICE_URL", "http://192.168.50.15:8102")
    print(f"🧠 Checking memory service at {memory_url}...")
    health_cmd = (f"curl -f {memory_url}/healthz || "
                  "echo 'Memory service not available'")
    run(health_cmd, dry=dry, check=False)

# ──────────────────────────────────────────────────────────────────────────────
# Docker builds (base + services) — preserves your original behavior
# ──────────────────────────────────────────────────────────────────────────────

def build_images(tag: str, push: bool, multi_arch: bool, dry=False):
    # Base image
    if multi_arch:
        base_cmd = [
            "docker","buildx","build",
            "-f","docker/Dockerfile",
            "--platform","linux/amd64,linux/arm64",
            "-t","owui/base:py311",".",
        ]
        base_cmd += ["--push"] if push else ["--load"]
        run(base_cmd, dry=dry)
    else:
        run(["docker","build","-f","docker/Dockerfile","-t","owui/base:py311","."], dry=dry)

    # Services in declared order
    for svc in SERVICES:
        context = (REPO_ROOT / svc)
        if not context.exists():
            print(f"• Skipping (missing dir): {svc}")
            continue
        parts = svc.split('-', 1)
        image_name = parts[1] if len(parts) > 1 else svc
        image = f"owui/{image_name}:{tag}"
        if multi_arch:
            cmd = [
                "docker","buildx","build",
                "--platform","linux/amd64,linux/arm64",
                "-t", image, str(context),
            ]
            cmd += ["--push"] if push else ["--load"]
            run(cmd, dry=dry)
        else:
            run(["docker","build","-t", image, str(context)], dry=dry)
            if push:
                run(["docker","push", image], dry=dry)
    print("• All service builds complete.")

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="git fetch/pull + pre-deploy tag")
    ap.add_argument("--deps",   action="store_true", help="install Python/Node deps")
    ap.add_argument("--config", action="store_true", help="ensure presets.json/tools.json")
    ap.add_argument("--test",   action="store_true", help="run tests (pytest / npm test)")
    ap.add_argument("--build",  action="store_true", help="build base + all services")
    ap.add_argument("--deploy", action="store_true", help="restart runtime and run integration test")
    ap.add_argument("--memory", action="store_true", help="deploy memory service to remote Docker host")
    ap.add_argument("--sanity", action="store_true", help="sanity checks (envs, n8n, memory health)")
    ap.add_argument("--all",    action="store_true", help="run everything in order")

    # original flags preserved
    ap.add_argument("--push", action="store_true", help="push images after build")
    ap.add_argument("--multi-arch", action="store_true", help="buildx for linux/amd64,arm64")
    ap.add_argument("--tag", default="dev", help="image tag (default: dev)")
    ap.add_argument("--dry-run", action="store_true", help="print commands only")

    # new behavior flags
    ap.add_argument("--memory-host", default="192.168.50.15", help="remote Docker host for memory service")
    ap.add_argument("--ignore-test-fail", action="store_true", help="do not fail if integration test fails")

    args = ap.parse_args()
    if not any([args.update, args.deps, args.config, args.test, args.build,
                args.deploy, args.memory, args.sanity, args.all]):
        # preserve old default behavior: build only
        args.build = True

    load_env()
    if args.all or args.sanity:
        check_envs()

    try:
        if args.all or args.update:
            git_update(args.dry_run)
        if args.all or args.deps:
            install_deps(args.dry_run)
        if args.all or args.config:
            ensure_config_files(args.dry_run)
        if args.all or args.test:
            run_tests(args.dry_run)
        if args.all or args.build:
            build_images(tag=args.tag, push=args.push,
                         multi_arch=args.multi_arch, dry=args.dry_run)
        if args.all or args.deploy:
            deploy(dry=args.dry_run, ignore_test_fail=args.ignore_test_fail)
        if args.all or args.memory:
            deploy_memory_service(args.memory_host, args.dry_run)
        if args.all or args.sanity:
            sanity_checks(args.dry_run)
        print("\n✅ Done.")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        raise SystemExit(2)

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
