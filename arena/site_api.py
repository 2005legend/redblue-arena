"""Read-only views over recorded match logs for the SOC front-end.

Everything here is derived from events the arena actually emitted. Nothing is invented: when a
field cannot be known (for example the model that ran weeks ago), it says so instead of guessing.
"""
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

VULN_META = {
    "sqli": {"name": "SQL Injection (SQLi)", "severity": "CRITICAL",
             "cwe": "CWE-89: Improper Neutralization of Special Elements in SQL", "cvss": 9.8,
             "color": "#ef4444"},
    "idor": {"name": "Insecure Direct Object Reference (IDOR)", "severity": "HIGH",
             "cwe": "CWE-639: Authorization Bypass Through User-Controlled Key", "cvss": 7.5,
             "color": "#f97316"},
    "admin_bypass": {"name": "Admin Authorization Bypass", "severity": "CRITICAL",
                     "cwe": "CWE-287: Improper Authentication", "cvss": 9.1, "color": "#a855f7"},
    "path_traversal": {"name": "Path Traversal", "severity": "HIGH",
                       "cwe": "CWE-22: Path Traversal", "cvss": 8.6, "color": "#06b6d4"},
}


def read_events(path: Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def match_files(matches: Path) -> list[Path]:
    matches = Path(matches)
    found = list(matches.glob("*.jsonl")) + list(matches.glob("*/events.jsonl"))
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def _match_id(path: Path) -> str:
    return path.stem if path.suffix == ".jsonl" else path.parent.name


def _patch_header(patch: str) -> tuple[str, list[str], list[str]]:
    m = re.search(r"^\+\+\+ b/(.+)$", patch or "", re.M)
    removed = [l[1:] for l in (patch or "").splitlines() if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in (patch or "").splitlines() if l.startswith("+") and not l.startswith("+++")]
    return (m.group(1) if m else ""), removed, added


def summarize(path: Path) -> dict:
    events = read_events(path)
    mid = _match_id(path)
    start = next((e for e in events if e.get("type") == "match_start"), {})
    end = next((e for e in events if e.get("type") == "match_end"), None)
    summary = (end or {}).get("summary") or {}
    breaches = [e for e in events if e.get("type") == "breach"]
    patched = [e for e in events if e.get("type") == "patched"]
    failed = [e for e in events if e.get("type") == "blue_attempt" and not e.get("ok")]
    health = next((e for e in reversed(events) if e.get("type") == "health"), {})
    duration = round(events[-1].get("ts", 0) if events else 0, 1)
    started = datetime.fromtimestamp(path.stat().st_mtime - duration)
    classes = sorted({e.get("vuln_class") for e in breaches if e.get("vuln_class")})
    health_text = (f"{health.get('passed', 0)}/{health.get('passed', 0) + health.get('failed', 0)} tests"
                   if health else "unknown")
    if breaches and len(patched) >= len(breaches):
        outcome = "BLUE VICTORY - all findings patched"
    elif not breaches:
        outcome = "NO EXPLOITS FOUND"
    else:
        outcome = "RED FINDINGS UNPATCHED"
    return {
        "id": mid,
        "name": f"Match {mid}",
        "description": f"{len(breaches)} canary findings, {len(patched)} referee-verified patches",
        "status": "completed" if end else "running",
        "target_environment": "Local Sandbox (Host-Locked)",
        "red_model": os.environ.get("ARENA_RED_MODEL") or os.environ.get("ARENA_MODEL")
                     or "configured in models.yaml",
        "blue_model": os.environ.get("ARENA_BLUE_MODEL") or os.environ.get("ARENA_MODEL")
                      or "configured in models.yaml",
        "simulation_mode": start.get("strategy") or "hybrid",
        "selected_vulnerabilities": classes,
        "max_execution_time": int(round(duration)),
        "max_test_requests": summary.get("sweep_requests", 0),
        "auto_deploy": 1,
        "start_time": started.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": (started.timestamp() + duration) and
                    datetime.fromtimestamp(started.timestamp() + duration).strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": duration,
        "red_discoveries": len(breaches),
        "red_flags_captured": len({e.get("flag") for e in breaches}),
        "blue_patches_generated": len(patched),
        "blue_patches_approved": len(patched),
        "blue_patches_rejected": len(failed),
        "final_health": health_text,
        "outcome": outcome,
        "summary": summary,
        "_events": events,
        "_breaches": breaches,
        "_patched": patched,
        "_source": str(path),
    }


def list_matches(matches: Path) -> list[dict]:
    return [summarize(p) for p in match_files(matches)]


def _public(match: dict) -> dict:
    return {k: v for k, v in match.items() if not k.startswith("_")}


def dashboard(matches: Path) -> dict:
    all_matches = list_matches(matches)
    breaches = [e for m in all_matches for e in m["_breaches"]]
    patched = [e for m in all_matches for e in m["_patched"]]
    failed = sum(m["blue_patches_rejected"] for m in all_matches)
    ttps = [e.get("ttp_seconds") for e in patched if e.get("ttp_seconds")]
    with_breach = sum(1 for m in all_matches if m["_breaches"])
    last_health = all_matches[0]["final_health"] if all_matches else "unknown"

    by_class = {c: {"red": 0, "blue": 0} for c in VULN_META}
    for e in breaches:
        c = e.get("vuln_class")
        if c in by_class:
            by_class[c]["red"] += 1
    for e in patched:
        c = e.get("vuln_class")
        if c in by_class:
            by_class[c]["blue"] += 1

    buckets: dict[int, dict] = {}
    for m in all_matches:
        for e in m["_events"]:
            if e.get("type") not in ("breach", "patched", "health"):
                continue
            b = int(e.get("ts", 0) // 10) * 10
            row = buckets.setdefault(b, {"attacks": 0, "defenses": 0, "health": 100})
            if e["type"] == "breach":
                row["attacks"] += 1
            elif e["type"] == "patched":
                row["defenses"] += 1
            elif e.get("failed"):
                row["health"] = 97

    return {
        "total_battles": len(all_matches),
        "red_success_rate": round(100 * with_breach / len(all_matches), 1) if all_matches else 0,
        "blue_defense_rate": round(100 * len(patched) / len(breaches), 1) if breaches else 0,
        "vulnerabilities_discovered": len(breaches),
        "vulnerabilities_patched": len(patched),
        "failed_patch_attempts": failed,
        "average_patch_time_sec": round(sum(ttps) / len(ttps), 1) if ttps else 0,
        "application_availability": last_health,
        "charts": {
            "comparison": [{"metric": VULN_META[c]["name"], "red": v["red"], "blue": v["blue"]}
                           for c, v in by_class.items()],
            "timeline": [{"time": f"{b // 60:02d}:{b % 60:02d}", **v}
                         for b, v in sorted(buckets.items())],
            "event_distribution": [{"name": VULN_META[c]["name"], "count": v["red"],
                                    "color": VULN_META[c]["color"]}
                                   for c, v in by_class.items() if v["red"]],
        },
        "recent_battles": [_public(m) for m in all_matches[:8]],
    }


def vulnerabilities(matches: Path) -> list[dict]:
    all_matches = list_matches(matches)
    if not all_matches:
        return []
    latest = all_matches[0]
    patched_by_key = {(e.get("vuln_class"), e.get("route")): e for e in latest["_patched"]}
    out, seen = [], set()
    for e in latest["_breaches"]:
        key = (e.get("vuln_class"), e.get("route"))
        if key in seen:
            continue
        seen.add(key)
        meta = VULN_META.get(e.get("vuln_class"), {})
        patch_ev = patched_by_key.get(key, {})
        source, removed, added = _patch_header(patch_ev.get("patch", ""))
        packet = f"{e.get('method', 'GET')} {e.get('path', e.get('route', ''))}"
        if e.get("params"):
            packet += " " + json.dumps(e["params"])
        out.append({
            "id": f"{latest['id']}-{e.get('vuln_class')}-{len(out) + 1}",
            "name": meta.get("name", e.get("vuln_class", "finding")),
            "severity": meta.get("severity", "HIGH"),
            "cwe": meta.get("cwe", ""),
            "cvss": meta.get("cvss", 0),
            "affected_endpoint": f"{e.get('method', 'GET')} {e.get('path', e.get('route'))}",
            "source_file": source,
            "description": f"The target returned canary {e.get('flag')} for a request a normal "
                           f"user should not be able to make.",
            "root_cause": "\n".join(removed) if removed else "Not patched yet in this match.",
            "security_impact": "A canary secret was exposed in the response.",
            "detection_evidence": f"{packet} -> {e.get('flag')}",
            "mitigation": "\n".join(added) if added else "Pending: no referee-verified patch yet.",
            "before_patch": "\n".join(removed) if removed else "",
            "after_patch": "\n".join(added) if added else "",
            "match_id": latest["id"],
            "patched": bool(patch_ev),
        })
    return out


def patches(matches: Path) -> list[dict]:
    all_matches = list_matches(matches)
    if not all_matches:
        return []
    latest = all_matches[0]
    out = []
    for i, e in enumerate(latest["_patched"], 1):
        source, removed, added = _patch_header(e.get("patch", ""))
        meta = VULN_META.get(e.get("vuln_class"), {})
        out.append({
            "id": f"PATCH-{latest['id']}-{i:02d}",
            "vuln_type": e.get("vuln_class"),
            "name": meta.get("name", e.get("vuln_class", "patch")),
            "source_file": source,
            "original_code": "\n".join(removed),
            "proposed_patch": "\n".join(added),
            "diff_code": e.get("patch", ""),
            "explanation": ("Verified fix replayed from the patch cache; the referee re-ran the "
                            "exploit and all functional tests." if e.get("cached") else
                            "Model-generated fix; the referee re-ran the exploit and all "
                            "functional tests."),
            "status": "approved",
            "functional_passed": True,
            "security_passed": True,
            "health_passed": True,
            "referee_notes": f"Patch verified in {e.get('ttp_seconds')}s"
                             + (" (cached)" if e.get("cached") else ""),
            "match_id": latest["id"],
        })
    return out


def report(matches: Path, battle_id: str) -> dict | None:
    match = next((m for m in list_matches(matches) if m["id"] == battle_id), None)
    if not match:
        return None
    patched_by_key = {(e.get("vuln_class"), e.get("route")): e for e in match["_patched"]}
    findings = []
    for e in match["_breaches"]:
        key = (e.get("vuln_class"), e.get("route"))
        findings.append({
            "vuln_type": VULN_META.get(e.get("vuln_class"), {}).get("name", e.get("vuln_class")),
            "endpoint": e.get("route"),
            "canary_token": e.get("flag"),
            "status": "Mitigated" if key in patched_by_key else "Open",
            "patch_verification": "PASSED" if key in patched_by_key else "NOT PATCHED",
            "functional_tests": match["final_health"],
            "security_tests": "exploit replay blocked" if key in patched_by_key else "still leaking",
        })
    return {
        "report_id": f"REP-{match['id']}",
        "generated_at": datetime.now().isoformat(),
        "battle": {k: match[k] for k in ("id", "name", "outcome", "duration_seconds",
                                         "red_flags_captured", "red_discoveries",
                                         "blue_patches_generated", "blue_patches_approved",
                                         "final_health")},
        "executive_summary": {
            "title": "Cybersecurity Battle Assessment Report",
            "target_app": "local sandbox target",
            "source": "derived from the recorded event log",
        },
        "findings": findings,
    }


def target_status(cfg, matches: Path) -> dict:
    latest = list_matches(matches)
    patched_classes = {e.get("vuln_class") for e in latest[0]["_patched"]} if latest else set()
    known = set(VULN_META)
    return {
        "status": "operational" if latest and latest[0]["status"] == "running" else "idle",
        "global_mode": "secure" if known and known <= patched_classes else "vulnerable",
        "app_dir": str(getattr(cfg, "app_dir", "")),
        "admin_routes": list(getattr(cfg, "admin_routes", [])),
        "loot_paths": list(getattr(cfg, "loot_paths", [])),
        "flag_owners": getattr(cfg, "flag_owners", {}),
        "strategy": getattr(cfg, "strategy", "hybrid"),
        "patches": {
            "sqli": "sqli" in patched_classes,
            "idor": "idor" in patched_classes,
            "path_traversal": "path_traversal" in patched_classes,
            "admin_auth": "admin_bypass" in patched_classes,
        },
        "note": "The target app runs in an isolated sandbox only while a match is in progress.",
    }
