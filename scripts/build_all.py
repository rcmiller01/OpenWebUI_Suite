"""Build base image and all service images in dependency-friendly order.

Usage:
  python scripts/build_all.py [--push] [--tag TAG]

Requires docker CLI.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

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

def run(cmd: list[str]):
    print(f"\n>> {' '.join(cmd)}")
    subprocess.check_call(cmd)

def main():
    push = "--push" in sys.argv
    multi_arch = "--multi-arch" in sys.argv
    tag = "dev"
    if "--tag" in sys.argv:
        i = sys.argv.index("--tag")
        try:
            tag = sys.argv[i + 1]
        except IndexError:
            print("--tag requires a value", file=sys.stderr)
            return 1
    root = Path(__file__).resolve().parent.parent
    # Build base image
    if multi_arch:
        base_cmd = [
            "docker", "buildx", "build",
            "-f", "docker/Dockerfile",
            "--platform", "linux/amd64,linux/arm64",
            "-t", "owui/base:py311",
            ".",
        ]
        base_cmd += ["--push"] if push else ["--load"]
        run(base_cmd)
    else:
        run([
            "docker", "build",
            "-f", "docker/Dockerfile",
            "-t", "owui/base:py311",
            ".",
        ])
    for svc in SERVICES:
        context = root / svc
        if not context.exists():
            continue
        parts = svc.split('-', 1)
        image_name = parts[1] if len(parts) > 1 else svc
        image = f"owui/{image_name}:{tag}"
        if multi_arch:
            cmd = [
                "docker", "buildx", "build",
                "--platform", "linux/amd64,linux/arm64",
                "-t", image,
                str(context),
            ]
            cmd += ["--push"] if push else ["--load"]
            run(cmd)
        else:
            run(["docker", "build", "-t", image, str(context)])
            if push:
                run(["docker", "push", image])
    print("All builds completed.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
