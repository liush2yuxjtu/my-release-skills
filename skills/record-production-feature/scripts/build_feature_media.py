#!/usr/bin/env python3
"""Encode continuous, source-hashed feature derivatives. Never certify product pixels.

Python 3.10+, FFmpeg and ffprobe; no recorder, model API, camera simulation or
network calls. See references/media-contract.md for the deliberately small schema.
"""
import argparse
import hashlib
import json
import math
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(value, name, minimum=0):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= minimum,
            f"{name} must be a finite number >= {minimum}")
    return float(value)


def integer(value, name, minimum=1):
    require(isinstance(value, int) and not isinstance(value, bool) and value >= minimum,
            f"{name} must be an integer >= {minimum}")
    return value


def interval(value, name, duration):
    require(isinstance(value, list) and len(value) == 2, f"{name} must be [start_s, end_s]")
    start, end = (number(v, name) for v in value)
    require(start < end <= duration + 0.001, f"{name} must fit the actual source duration")
    return [start, end]


def command(args, timeout=60):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, f"{args[0]} failed: {result.stderr.strip()[-2000:]}")
    return result.stdout


def probe(path):
    data = json.loads(command(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                               "-of", "json", str(path)]))
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    require(video is not None, "Source has no video stream")
    require(not video.get("disposition", {}).get("attached_pic"), "Source is a cover image, not video")
    duration = number(float(data.get("format", {}).get("duration", 0)), "media duration", 0.001)
    video_duration = number(float(video.get("duration", duration)), "video duration", 0.001)
    require(not any(float(video.get("tags", {}).get(k, 0)) for k in ("rotate",)),
            "Rotated source needs an explicitly normalized, separately preserved source")
    require(not any(s.get("rotation", 0) for s in video.get("side_data_list", [])),
            "Rotated source needs an explicitly normalized, separately preserved source")
    return {"duration_s": duration, "video_duration_s": video_duration,
            "width": int(video["width"]), "height": int(video["height"]),
            "codec": video["codec_name"], "pix_fmt": video.get("pix_fmt"),
            "audio_streams": sum(s.get("codec_type") == "audio" for s in data["streams"])}


def rectangle(value, name, width, height):
    require(isinstance(value, list) and len(value) == 4, f"{name} must be [x, y, width, height] in source pixels")
    x, y, w, h = [integer(v, name, 0 if i < 2 else 1) for i, v in enumerate(value)]
    require(x + w <= width and y + h <= height, f"{name} exceeds actual source dimensions")
    return [x, y, w, h]


def read_model(manifest, root, source_hash, source_kind, metadata):
    require("model_execution" in manifest, "Explicit model_execution is required; never infer live or no inference")
    summary = manifest["model_execution"]
    if summary is None:
        reason = manifest.get("no_inference_reason")
        require(isinstance(reason, str) and reason.strip(), "model_execution=null requires an observed no_inference_reason")
        return None, None
    require(isinstance(summary, dict), "model_execution must be null or an evidence summary")
    require(summary.get("mode") in ("live", "captured-replay"), "Only real live or captured-replay model provenance is allowed")
    for field in ("operation", "run_id", "evidence", "current_live_e2e", "source_live_e2e", "disclosure"):
        require(field in summary, f"model_execution.{field} is required")
    require(isinstance(summary["run_id"], str) and summary["run_id"].strip(), "model_execution.run_id is required")
    source_live = summary["source_live_e2e"]
    require(source_live is None or (isinstance(source_live, dict)
            and source_live.get("status") in ("pass", "fail", "blocked", "pending", "not-run")),
            "source_live_e2e must be null or an explicit source status object")
    operation = summary["operation"]
    require(operation in ("fresh-recording", "reuse", "re-edit", "replay-recording"), "Invalid model_execution.operation")
    if operation in ("reuse", "re-edit"):
        require(summary["current_live_e2e"] == "not-run", "reuse/re-edit current_live_e2e must remain not-run")
        require(isinstance(summary.get("edit_run_id"), str) and summary["edit_run_id"].strip(),
                "reuse/re-edit requires a separate edit_run_id")
    else:
        expected_mode = "live" if operation == "fresh-recording" else "captured-replay"
        require(summary["mode"] == expected_mode, f"{operation} requires mode={expected_mode}")
    require(isinstance(summary["evidence"], str), "model_execution.evidence must name a real JSON file")
    evidence_path = (root / summary["evidence"]).resolve()
    evidence = json.loads(evidence_path.read_text())
    require(isinstance(evidence, dict), "Model evidence must be a JSON object")
    require(evidence.get("schema") == "feature-model-execution/v1", "Unsupported model evidence schema")
    fields = ("mode", "run_id") if operation in ("reuse", "re-edit") else ("mode", "run_id", "current_live_e2e", "source_live_e2e")
    for field in fields:
        require(summary[field] == evidence.get(field), f"model_execution.{field} differs from its evidence")
    require(summary["current_live_e2e"] in ("not-run", "pass", "fail", "blocked"), "Invalid current_live_e2e")
    disclosure = evidence.get("disclosure", {})
    require(isinstance(disclosure, dict) and summary["disclosure"] == disclosure.get("label"),
            "model_execution.disclosure must match the original evidence label")
    require(isinstance(evidence.get("raw"), dict), "Model evidence raw must be an object")
    raw_hash = evidence["raw"].get("sha256")
    origin_hash = source_hash if source_kind == "full-recording" else manifest["source"].get("origin_raw_sha256")
    require(isinstance(raw_hash, str) and len(raw_hash) == 64
            and all(c in "0123456789abcdef" for c in raw_hash) and raw_hash == origin_hash,
            "Model evidence raw SHA-256 must match this source (or explicit derivative origin_raw_sha256)")
    replay_rect = None
    if summary["mode"] == "captured-replay":
        require(summary["current_live_e2e"] == "not-run", "captured-replay current_live_e2e must remain not-run")
        require(evidence.get("current_live_e2e") == "not-run", "Original captured-replay evidence cannot claim a current live E2E result")
        require(source_live == evidence.get("source_live_e2e"), "Historical replay source_live_e2e must match the original replay evidence")
        require(isinstance(summary["source_live_e2e"], dict)
                and summary["source_live_e2e"].get("status") == "pass",
                "captured-replay requires the original source_live_e2e pass receipt")
        require(disclosure.get("label") == "Recorded model response · real tools", "Required replay disclosure label is missing")
        visible_evidence = disclosure.get("visible_evidence")
        require(isinstance(visible_evidence, str) and (root / visible_evidence).is_file(),
                "Replay requires existing native-label visible_evidence (relative to the manifest run)")
        require(isinstance(manifest.get("replay_disclosure"), dict), "replay_disclosure.source_rect_px is required")
        replay_rect = rectangle(manifest["replay_disclosure"].get("source_rect_px"),
                                "replay_disclosure.source_rect_px", metadata["width"], metadata["height"])
    elif operation == "fresh-recording":
        require(summary["source_live_e2e"] is None, "live source_live_e2e must be null")
    elif source_live and source_live["status"] == "pass":
        require(source_live.get("run_id") == evidence["run_id"], "Historical live receipt must identify the original source run")
        require(evidence.get("current_live_e2e") == "pass", "Historical source pass conflicts with the original live evidence status")
    # Copy the supplied facts, not a newly inferred live status. Hashes establish
    # identity only: request matching, real tools and label pixels still need QA.
    outcome = evidence.get("outcome")
    return {**summary, "evidence_sha256": sha256(evidence_path),
            "source_evidence_current_live_e2e": evidence.get("current_live_e2e"),
            "source_evidence_outcome": outcome.get("status") if isinstance(outcome, dict) else None,
            "checks": "schema-consistency-and-source-hash-only; provenance-review-required"}, replay_rect


def make_plan(args):
    require(sys.version_info >= (3, 10), "Python 3.10+ required")
    require(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe are required; run scripts/preflight.py")
    require(args.execution_route != "mac-mini" or platform.system() == "Darwin", "mac-mini requires actual Darwin; use work for Cloud/Work")
    require(args.expected_host is None or args.expected_host == socket.gethostname(), "--expected-host differs from the actual hostname")
    manifest_path = Path(args.manifest).resolve()
    require(not Path(args.output).is_symlink(), "Output path already exists as a symlink; choose a new edits/vN directory")
    output = Path(args.output).resolve()
    require(not output.exists(), "Output path already exists; choose a new edits/vN directory")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    require(isinstance(manifest, dict) and manifest.get("schema") == "feature-media/v1", "Manifest schema must be feature-media/v1")
    for key in ("feature_id", "run_id"):
        require(isinstance(manifest.get(key), str) and manifest[key].strip(), f"{key} is required")
    source = manifest.get("source", {})
    require(isinstance(source, dict) and isinstance(source.get("path"), str), "source.path is required")
    source_path = (manifest_path.parent / source["path"]).resolve()
    require(source_path.is_file(), f"Source file is missing: {source_path}")
    require(source.get("kind") in ("full-recording", "existing-derivative"), "Declare source.kind as full-recording or existing-derivative")
    source_hash = sha256(source_path)
    require(source.get("sha256") == source_hash, "source.sha256 does not match the immutable source bytes")
    metadata = probe(source_path)
    formats = ["mp4", "gif"] if args.format == "both" else [args.format]
    if "mp4" in formats:
        require(source["kind"] == "full-recording" and source.get("complete") is True,
                "Full MP4 requires a complete full-recording; existing derivatives cannot substitute for missing originals")
        require(metadata["codec"] not in ("gif", "png", "mjpeg", "webp"), "An image/GIF cannot be relabeled as a full original recording")
    proof = interval(manifest.get("proof_interval_s"), "proof_interval_s", metadata["video_duration_s"])
    require(proof[1] - proof[0] >= 3 - 0.001, "Declared source result interval must last at least 3 continuous seconds")
    model, replay_rect = read_model(manifest, manifest_path.parent, source_hash, source["kind"], metadata)
    require(not args.fixture or model is None, "Codec fixtures cannot carry or simulate product model provenance")
    edits = []
    for kind in formats:
        settings = manifest.get(kind, {})
        require(isinstance(settings, dict), f"{kind} settings must be an object")
        forbidden = set(settings) - ({"crop_px", "width"} if kind == "mp4" else
                                      {"crop_px", "width", "start_s", "duration_s", "fps", "max_bytes"})
        require(not forbidden, f"Unsupported {kind} settings: {sorted(forbidden)}; camera keyframes, holds and speed changes are not supported")
        crop = rectangle(settings.get("crop_px", [0, 0, metadata["width"], metadata["height"]]),
                         f"{kind}.crop_px", metadata["width"], metadata["height"])
        width = integer(settings.get("width", crop[2] - crop[2] % 2 if kind == "mp4" else 520), f"{kind}.width", 2)
        require(kind != "mp4" or width % 2 == 0, "mp4.width must be even for yuv420p")
        start, duration = 0.0, metadata["video_duration_s"]
        edit = {"kind": kind, "crop_px": crop, "width": width}
        if kind == "gif":
            start = number(settings.get("start_s", 0), "gif.start_s")
            duration = number(settings.get("duration_s", 8), "gif.duration_s", 0.001)
            require(start + duration <= metadata["video_duration_s"] + 0.001, "GIF interval exceeds actual source video duration")
            require(start <= proof[0] + 0.001 and proof[1] <= start + duration + 0.001,
                    "GIF window must contain the complete declared 3-second result interval")
            fps = integer(settings.get("fps", 12), "gif.fps")
            require(fps <= 30, "gif.fps must be <=30")
            edit.update(fps_candidates=list(dict.fromkeys([fps] + [n for n in (10, 8) if n < fps])),
                        max_bytes=integer(settings.get("max_bytes", 3 * 1024 * 1024), "gif.max_bytes"))
        edit.update(start_s=start, duration_s=duration, source_interval_s=[start, start + duration],
                    time_map={"kind": "continuous-source", "source_start_s": start,
                              "speed": 1, "editorial_hold_s": 0})
        if replay_rect:
            x, y, w, h = crop
            rx, ry, rw, rh = replay_rect
            require(x <= rx and y <= ry and rx + rw <= x + w and ry + rh <= y + h,
                    f"{kind} crop would remove the mandatory native replay disclosure")
            projected_height = rh * width / w
            threshold = number(manifest.get("replay_disclosure", {}).get("min_output_height_px", 12),
                               "replay_disclosure.min_output_height_px", 12)
            require(projected_height >= threshold, f"{kind} scales replay disclosure below its configured minimum pixel height")
            edit["replay_disclosure"] = {"source_rect_px": replay_rect,
                                         "projected_region_height_px": projected_height,
                                         "visual_readability": "pending"}
        edits.append(edit)
    return {"manifest": manifest, "manifest_path": manifest_path, "manifest_bytes": manifest_bytes, "output": output,
            "source_path": source_path, "source_sha256": source_hash, "source_probe": metadata,
            "model_execution": model, "edits": edits}


def base_command(plan):
    args = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-n", "-threads", "1",
            "-filter_threads", "1", "-filter_complex_threads", "1"]
    if plan["source_probe"]["codec"] == "gif":
        args += ["-ignore_loop", "1"]
    return args + ["-i", str(plan["source_path"])]


def filters(edit):
    x, y, w, h = edit["crop_px"]
    height = "-2" if edit["kind"] == "mp4" else "-1"
    return f"crop={w}:{h}:{x}:{y}:exact=1,scale={edit['width']}:{height}:flags=lanczos,setsar=1"


def encode(plan, args):
    output = plan["output"]
    output.mkdir(parents=True, exist_ok=False)
    (output / "attempts").mkdir()
    with (output / "input-manifest.json").open("xb") as target:
        target.write(plan["manifest_bytes"])
    receipt = {"schema": "feature-media-build/v1", "status": "failed", "fixture_only": args.fixture,
               "feature_id": plan["manifest"]["feature_id"], "run_id": plan["manifest"]["run_id"],
               "input_manifest_sha256": sha256(output / "input-manifest.json"),
               "execution": {"route": args.execution_route, "hostname": socket.gethostname(),
                             "platform": platform.system(), "ffmpeg": "unreported"},
               "source": {**plan["manifest"]["source"], "resolved_path": str(plan["source_path"]),
                          "sha256_before": plan["source_sha256"], "probe": plan["source_probe"]},
               "model_execution": plan["model_execution"],
               "no_inference_reason": plan["manifest"].get("no_inference_reason"),
               "declared_proof_interval_s": plan["manifest"]["proof_interval_s"],
               "plan": plan["edits"], "attempts": [], "outputs": [],
               "visual_review": "pending", "product_e2e": "not-assessed-by-encoder"}
    receipt["gates"] = {"source_provenance": "pending", "model_provenance": "pending" if plan["model_execution"] else "no-inference-declared-unreviewed",
                        "production": "pending", "visual": "pending", "player": "pending",
                        "independent_review": "pending", "reading_time": "pending"}

    def run_encode(cmd, relative):
        log = output / (relative + ".stderr.txt")
        attempt = {"path": relative, "command": cmd, "stderr": str(log.relative_to(output))}
        receipt["attempts"].append(attempt)
        with log.open("x") as stderr:
            try:
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=stderr, timeout=args.timeout_s)
                attempt["returncode"] = result.returncode
                require(result.returncode == 0, f"Encoding failed; inspect {log}")
            except subprocess.TimeoutExpired as error:
                attempt["timed_out_s"] = args.timeout_s
                raise Invalid(f"Encoding exceeded --timeout-s={args.timeout_s}; partial output preserved") from error
        path = output / relative
        attempt.update(sha256=sha256(path), bytes=path.stat().st_size)
        return path

    try:
        receipt["execution"]["ffmpeg"] = command(["ffmpeg", "-version"]).splitlines()[0]
        for edit in plan["edits"]:
            base = base_command(plan)
            if edit["kind"] == "mp4":
                cmd = base + ["-map", "0:v:0", "-map", "0:a?", "-vf", filters(edit),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-threads", "1",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1",
                              "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
                              "-movflags", "+faststart", str(output / "demo.mp4")]
                selected = run_encode(cmd, "demo.mp4")
            else:
                selected = None
                for fps in edit["fps_candidates"]:
                    relative = f"attempts/gif-{fps}fps.gif"
                    # A single continuous interval; palette generation cannot invent UI frames.
                    graph = (f"trim=start={edit['start_s']:.9f}:duration={edit['duration_s']:.9f},"
                             f"setpts=PTS-STARTPTS,fps={fps}:round=near,{filters(edit)},split[a][b];"
                             "[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a")
                    candidate = run_encode(base + ["-filter_complex", graph, "-an", "-loop", "0",
                                                   "-map_metadata", "-1", str(output / relative)], relative)
                    attempt = receipt["attempts"][-1]
                    attempt.update(fps=fps, budget_bytes=edit["max_bytes"],
                                   within_budget=candidate.stat().st_size <= edit["max_bytes"])
                    if attempt["within_budget"]:
                        selected = output / "feature.gif"
                        with candidate.open("rb") as source, selected.open("xb") as target:
                            shutil.copyfileobj(source, target)
                        edit["selected_fps"] = fps
                        break
                require(selected is not None, "GIF remains above max_bytes at every configured FPS; attempts preserved, no width reduced")
            metadata = probe(selected)
            expected = plan["source_probe"]["duration_s"] if edit["kind"] == "mp4" else edit["duration_s"]
            tolerance = max(0.15, 1.5 / edit.get("selected_fps", 30))
            require(abs(metadata["duration_s"] - expected) <= tolerance, "Encoded duration differs from the continuous source interval")
            require(metadata["width"] == edit["width"], "Encoded width differs from the requested crop/scale")
            if edit["kind"] == "mp4":
                require(metadata["codec"] == "h264" and metadata["pix_fmt"] == "yuv420p", "MP4 codec contract failed")
                require(metadata["audio_streams"] == plan["source_probe"]["audio_streams"], "MP4 dropped a source audio stream")
            receipt["outputs"].append({"path": selected.name, "kind": edit["kind"],
                                       "role": "full-recording-derivative" if edit["kind"] == "mp4" else "continuous-excerpt",
                                       "sha256": sha256(selected), "bytes": selected.stat().st_size,
                                       "probe": metadata, "time_map": edit["time_map"],
                                       "sampling": "original-timestamps" if edit["kind"] == "mp4" else
                                                   f"{edit['selected_fps']}fps; GIF delays quantized to centiseconds"})
        receipt["status"] = "fixture-only" if args.fixture else "needs-visual-review"
        if plan["model_execution"] and plan["model_execution"]["current_live_e2e"] in ("fail", "blocked"):
            receipt["status"] = "blocked"
        if plan["model_execution"] and (plan["model_execution"]["source_evidence_current_live_e2e"] in ("fail", "blocked")
                                         or plan["model_execution"]["source_evidence_outcome"] in ("fail", "failed", "blocked")):
            receipt["status"] = "blocked"
            receipt["gates"]["source_provenance"] = "blocked: original model evidence records failure"
        if plan["model_execution"] and plan["model_execution"]["operation"] in ("reuse", "re-edit") and (not plan["model_execution"]["source_live_e2e"] or plan["model_execution"]["source_live_e2e"].get("status") != "pass"):
            receipt["status"] = "blocked"
            receipt["gates"]["source_provenance"] = "blocked: original live verification not supplied"
    except Exception as error:
        receipt["error"] = str(error)
    finally:
        try:
            receipt["source"]["sha256_after"] = sha256(plan["source_path"])
        except OSError as error:
            receipt["source"]["sha256_after"] = None
            receipt["source"]["postcheck_error"] = str(error)
        receipt["source"]["unchanged"] = receipt["source"]["sha256_after"] == plan["source_sha256"]
        if not receipt["source"]["unchanged"]:
            receipt.update(status="failed", error="Immutable source changed during encoding")
        # Retain hashes of partial files too; do not erase a failed attempt.
        for attempt in receipt["attempts"]:
            path = output / attempt["path"]
            if path.is_file():
                attempt.update(sha256=sha256(path), bytes=path.stat().st_size)
        with (output / "manifest.json").open("x") as stream:
            json.dump(receipt, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="feature-media/v1 JSON; paths relative to this file")
    parser.add_argument("--output", required=True, help="NEW edits/vN directory; existing paths are refused")
    parser.add_argument("--execution-route", choices=("work", "mac-mini"), default="work")
    parser.add_argument("--expected-host", help="Optional assertion against the actual hostname")
    parser.add_argument("--format", choices=("mp4", "gif", "both"), default="both")
    parser.add_argument("--dry-run", action="store_true", help="Validate and probe, without creating output files")
    parser.add_argument("--fixture", action="store_true", help="Isolated codec tests only; never product evidence")
    parser.add_argument("--timeout-s", type=int, default=300, help="Per encoding attempt (1–3600 seconds)")
    args = parser.parse_args(argv)
    try:
        require(1 <= args.timeout_s <= 3600, "--timeout-s must be 1–3600")
        plan = make_plan(args)
        if args.dry_run:
            result = {"schema": "feature-media-plan/v1", "status": "valid-plan", "fixture_only": args.fixture,
                      "source_sha256": plan["source_sha256"], "source_probe": plan["source_probe"],
                      "output": str(plan["output"]), "edits": plan["edits"],
                      "model_execution": plan["model_execution"], "visual_review": "pending"}
        else:
            result = encode(plan, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["status"] in ("failed", "blocked") else 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"schema": "feature-media-build/v1", "status": "blocked", "error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
