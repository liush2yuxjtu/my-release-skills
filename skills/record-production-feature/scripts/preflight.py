#!/usr/bin/env python3
"""Report concrete package/dependency gaps before research, recording or encoding.

This inspects the selected machine. It never establishes UI access, model success,
production deployment, recorder readiness or visual quality. No dependencies are
installed and no browser/model session is launched.
"""
import argparse
import importlib.util
import json
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path


COMMON_FILES = ["SKILL.md", "scripts/preflight.py", "scripts/build_feature_media.py",
                "assets/feature.template.json", "references/media-contract.md",
                "references/cinematography.md", "references/model-execution.md",
                "playbooks/live-model-recording.md", "playbooks/captured-model-replay.md",
                "assets/model-execution.live.template.json", "assets/model-execution.replay.template.json"]


def run(command, cwd=None):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=20)


def inspect(args):
    package = Path(__file__).resolve().parent.parent
    project = Path(args.project).resolve()
    formats = ["mp4", "gif"] if args.format == "both" else [args.format]
    result = {"schema": "feature-media-preflight/v1", "status": "blocked", "phase": args.phase,
              "formats": formats, "route": args.execution_route,
              "machine": {"platform": platform.system(), "hostname": socket.gethostname(),
                          "project": str(project), "python": platform.python_version()},
              "checks": [], "gaps": [],
              "unassessed": ["production source and version", "actual UI/login and recorder operation",
                             "model/capture provenance and actual authorized product calls",
                             "native replay disclosure pixels", "visual, reading-time and independent review"]}

    def check(name, ok, observed=None, remedy=None):
        result["checks"].append({"name": name, "ok": bool(ok), "observed": observed})
        if not ok:
            result["gaps"].append({"name": name, "observed": observed, "remedy": remedy})

    required = list(COMMON_FILES)
    if args.phase == "verify":
        required += ["scripts/verify_delivery.py", "references/delivered-video-verification.md"]
        if "mp4" in formats:
            required += ["scripts/verify_playback.mjs"]
        if "gif" in formats:
            required += ["scripts/verify_legibility.py", "scripts/legibility_spec.example.json"]
    missing = [name for name in required if not (package / name).is_file()]
    check("package-files", not missing, {"missing": missing}, "Restore the named files from this skill package")
    check("python", sys.version_info >= (3, 10), platform.python_version(), "Use Python 3.10 or later")
    check("execution-route", args.execution_route != "mac-mini" or platform.system() == "Darwin",
          {"route": args.execution_route, "actual_platform": platform.system()},
          "Use work for Cloud/Work; mac-mini requires an actual Darwin host")
    check("expected-host", not args.expected_host or args.expected_host == socket.gethostname(),
          {"expected": args.expected_host, "actual": socket.gethostname()},
          "Use the measured hostname of the selected execution machine")
    check("project-directory", project.is_dir(), str(project), "Select an existing isolated project directory with --project")
    if project.is_dir():
        free = shutil.disk_usage(project).free
        result["machine"]["free_bytes"] = free
        check("free-space", free >= args.min_free_gib * 1024 ** 3,
              {"free_bytes": free, "required_gib": args.min_free_gib}, "Free space on the selected execution filesystem")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    check("ffmpeg", ffmpeg is not None, ffmpeg, "Install FFmpeg on the selected execution machine")
    check("ffprobe", ffprobe is not None, ffprobe, "Install ffprobe from the matching FFmpeg distribution")
    if ffmpeg:
        try:
            version = run([ffmpeg, "-version"])
            check("ffmpeg-runnable", version.returncode == 0, version.stdout.splitlines()[:1], "Repair the FFmpeg executable")
            filters = run([ffmpeg, "-hide_banner", "-filters"])
            encoders = run([ffmpeg, "-hide_banner", "-encoders"])
            needed_filters = ["crop", "scale", "setsar"]
            if "gif" in formats:
                needed_filters += ["trim", "setpts", "fps", "split", "palettegen", "paletteuse"]
            available_filters = {line.split()[1] for line in filters.stdout.splitlines() if len(line.split()) >= 3}
            available_encoders = {line.split()[1] for line in encoders.stdout.splitlines() if len(line.split()) >= 3}
            missing_filters = sorted(set(needed_filters) - available_filters)
            needed_encoders = (["libx264", "aac"] if "mp4" in formats else []) + (["gif"] if "gif" in formats else [])
            missing_encoders = sorted(set(needed_encoders) - available_encoders)
            if args.phase != "verify":
                check("ffmpeg-filters", filters.returncode == 0 and not missing_filters,
                      {"missing": missing_filters}, "Use an FFmpeg build with the named filters")
                check("ffmpeg-encoders", encoders.returncode == 0 and not missing_encoders,
                      {"missing": missing_encoders}, "Use an FFmpeg build with the named encoders")
        except (OSError, subprocess.SubprocessError) as error:
            check("ffmpeg-inspection", False, str(error), "Repair or replace the FFmpeg executable")
    if ffprobe:
        try:
            version = run([ffprobe, "-version"])
            check("ffprobe-runnable", version.returncode == 0, version.stdout.splitlines()[:1], "Repair ffprobe")
        except (OSError, subprocess.SubprocessError) as error:
            check("ffprobe-runnable", False, str(error), "Repair ffprobe")

    if args.phase == "verify":
        check("pillow", importlib.util.find_spec("PIL") is not None, None, "Install Pillow in this Python environment")
        if "gif" in formats:
            executable = shutil.which("tesseract")
            check("tesseract", executable is not None, executable, "Install Tesseract 5 and the requested OCR language data")
            if executable:
                try:
                    version = run([executable, "--version"])
                    first_line = version.stdout.splitlines()[0] if version.stdout else ""
                    major = int(first_line.split()[1].split(".")[0])
                    check("tesseract-version", version.returncode == 0 and major >= 5, first_line, "Use Tesseract 5 or later")
                    languages = run([executable, "--list-langs"])
                    missing_languages = sorted(set(args.ocr_languages.split("+")) - set(languages.stdout.splitlines()[1:]))
                    check("ocr-languages", languages.returncode == 0 and not missing_languages,
                          {"missing": missing_languages}, "Install the named OCR language packs; do not treat missing OCR as PASS")
                except (ValueError, IndexError, OSError, subprocess.SubprocessError) as error:
                    check("tesseract-inspection", False, str(error), "Repair Tesseract and its language data")

    if args.phase == "record" or (args.phase == "verify" and "mp4" in formats):
        node = shutil.which("node")
        check("node", node is not None, node, "Install Node.js for the actual Playwright recorder/player route")
        if node and project.is_dir():
            # Same resolver and explicit environment overrides as verify_playback.mjs.
            script = """
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
try {
  const resolve = createRequire(path.join(process.cwd(), 'package.json'));
  const modulePath = process.env.PLAYWRIGHT_MODULE_PATH;
  const resolved = resolve.resolve(modulePath ? path.resolve(modulePath) : 'playwright');
  const pw = resolve(resolved);
  if (!pw.chromium) throw Error('Resolved module has no Chromium API');
  const executable = path.resolve(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || pw.chromium.executablePath());
  console.log(JSON.stringify({node:process.version,module:resolved,executable,
    executable_exists:fs.existsSync(executable)}));
} catch (error) { console.log(JSON.stringify({error:String(error)})); process.exitCode=1; }
"""
            try:
                checked = run([node, "-e", script], project)
                observed = json.loads(checked.stdout)
                check("project-playwright", checked.returncode == 0, observed,
                      "Use project-local playwright, or set PLAYWRIGHT_MODULE_PATH to an existing module directory/entry filesystem path; package names are not accepted as overrides")
                if checked.returncode == 0:
                    check("chromium-executable", observed["executable_exists"], observed["executable"],
                          "Install the matching Chromium or set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH to the verified executable")
                    if observed["executable_exists"]:
                        version = run([observed["executable"], "--version"])
                        check("chromium-version", version.returncode == 0, version.stdout.strip(), "Repair the selected browser executable")
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                check("playwright-inspection", False, str(error), "Repair the project-local Playwright/Chromium route")
    result["status"] = "dependencies-ready" if not result["gaps"] else "blocked"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("encode", "record", "verify"), default="encode")
    parser.add_argument("--format", choices=("mp4", "gif", "both"), default="both")
    parser.add_argument("--execution-route", choices=("work", "mac-mini"), default="work")
    parser.add_argument("--expected-host")
    parser.add_argument("--project", default=".", help="Actual project; Node modules resolve here")
    parser.add_argument("--min-free-gib", type=float, default=10)
    parser.add_argument("--ocr-languages", default="eng", help="Tesseract language codes joined by +")
    parser.add_argument("--json", action="store_true", help="Compatibility flag; output is always JSON")
    args = parser.parse_args(argv)
    if not (0 <= args.min_free_gib <= 1000000):
        parser.error("--min-free-gib must be a finite nonnegative number")
    result = inspect(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "dependencies-ready" else 1


if __name__ == "__main__":
    sys.exit(main())
