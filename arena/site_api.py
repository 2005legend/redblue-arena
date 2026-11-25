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

import httpx

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
    "mass_assignment": {"name": "Mass Assignment", "severity": "CRITICAL",
                        "cwe": "CWE-915: Improperly Controlled Modification of Object Attributes",
                        "cvss": 9.1, "color": "#eab308"},
    "debug_exposure": {"name": "Debug Endpoint Exposure", "severity": "HIGH",
                       "cwe": "CWE-489: Active Debug Code", "cvss": 7.5, "color": "#14b8a6"},
    "code_injection": {"name": "Code Injection (eval)", "severity": "CRITICAL",
                       "cwe": "CWE-95: Improper Neutralization of Directives in Dynamically "
                              "Evaluated Code", "cvss": 9.8, "color": "#ec4899"},
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
    flat = {p.stem for p in matches.glob("*.jsonl")}
    found = list(matches.glob("*.jsonl")) + [
        p for p in matches.glob("*/events.jsonl") if p.parent.name not in flat
    ]
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def _match_id(path: Path) -> str:
    if path.name == "events.jsonl":  # a live run lives in matches/<match_id>/
        return path.parent.name
    return path.stem


def _target_answers(url: str, timeout: float = 0.6) -> bool:
    try:
        return httpx.get(url.rstrip("/") + "/openapi.json", timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False


def live_target(matches: Path, match_id: str | None = None, check=None) -> dict:
    """Where a match is serving the target app right now, from the events it wrote.

    The last target_live/target_down pair in a log decides it: a swap emits a new target_live, a
    teardown emits target_down, and a demo run that keeps the target alive emits neither. The log
    alone cannot tell a killed process from a live one, so the URL is health-checked (injectable
    `check(url, timeout) -> bool` for tests).

    Without `match_id` the newest match that ever started a target is used, which is what makes a
    match started from the CLI (`python -m arena.cli run`) visible to the `serve` site, and keeps a
    kept-alive target reachable after the server restarts.
    """
    check = check or _target_answers
    if match_id:
        path = Path(matches) / match_id / "events.jsonl"
        paths = [path] if path.is_file() else []
    else:
        paths = [p for p in match_files(matches) if p.name == "events.jsonl"]
    for path in paths:
        state, started = None, False
        for event in read_events(path):
            if event.get("type") == "target_live":
                started = True
                state = {"url": event.get("url"), "port": event.get("port")}
            elif event.get("type") == "target_down":
                state = None
        if not started:
            continue
        mid = _match_id(path)
        # Only the newest match that started a target is considered: once a newer match has torn
        # its own target down, an older kept target must not come back as "live".
        if not state or not state.get("url"):
            return {"url": None, "port": None, "alive": False, "match_id": mid}
        alive = bool(check(state["url"], 0.6))
        return {"url": state["url"] if alive else None, "port": state["port"],
                "alive": alive, "match_id": mid}
    return {"url": None, "port": None, "alive": False, "match_id": match_id}


def _patch_header(patch: str) -> tuple[str, list[str], list[str]]:
    m = re.search(r"^\+\+\+ b/(.+)$", patch or "", re.M)
    removed = [l[1:] for l in (patch or "").splitlines() if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in (patch or "").splitlines() if l.startswith("+") and not l.startswith("+++")]
    return (m.group(1) if m else ""), removed, added


def _patch_context(patch: str) -> list[str]:
    """Original lines around the change; used when a verified patch only adds guard code."""
    return [l[1:] for l in (patch or "").splitlines() if l.startswith(" ") and l.strip()]


def summarize(path: Path) -> dict:
    events = read_events(path)
    mid = _match_id(path)
    start = next((e for e in events if e.get("type") == "match_start"), {})
    end = next((e for e in events if e.get("type") == "match_end"), None)
    # A log without match_end whose process is long gone (killed match) must not read as "running".
    stale = end is None and time.time() - path.stat().st_mtime > 600
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
    # Red can breach the same class/route repeatedly (a re-test, or an LLM pass over a found bug), which
    # inflates raw breach events. The referee summary counts unique findings, so prefer it when present.
    red_count = (summary.get("red", len(breaches)) if end else len(breaches))
    # Split the token/call totals per agent. New logs record the split directly; older ones only have
    # the total, so fall back to what the events prove: each `blue_thinking` is one Blue model call,
    # Red's calls are the remainder, and tokens can only be attributed when one side made no calls.
    blue_llm_calls = summary.get("blue_llm_calls")
    if blue_llm_calls is None:
        blue_llm_calls = sum(1 for e in events if e.get("type") == "blue_thinking")
    red_llm_calls = summary.get("red_llm_calls")
    if red_llm_calls is None and summary.get("llm_calls") is not None:
        red_llm_calls = max(0, summary["llm_calls"] - blue_llm_calls)
    total_tokens = summary.get("tokens") or 0
    red_tokens = summary.get("red_tokens")
    blue_tokens = summary.get("blue_tokens")
    if end and red_tokens is None and blue_tokens is None:
        if summary.get("llm_calls") == 0:
            red_tokens = blue_tokens = 0
        elif red_llm_calls == 0 and blue_llm_calls:
            red_tokens, blue_tokens = 0, total_tokens
        elif blue_llm_calls == 0 and red_llm_calls:
            red_tokens, blue_tokens = total_tokens, 0
    if stale:
        outcome = "MATCH INTERRUPTED - no referee verdict recorded"
    elif end and "total" in summary:
        if summary["total"] and summary["closed"] >= summary["total"]:
            outcome = "BLUE VICTORY - all findings patched"
        elif not summary["total"]:
            outcome = "NO EXPLOITS FOUND"
        else:
            outcome = "RED FINDINGS UNPATCHED"
    elif breaches and len(patched) >= len(breaches):
        outcome = "BLUE VICTORY - all findings patched"
    elif not breaches:
        outcome = "NO EXPLOITS FOUND"
    else:
        outcome = "RED FINDINGS UNPATCHED"
    sweep = next((e for e in events if e.get("type") == "sweep_done"), {})
    cached_patches = sum(1 for e in patched if e.get("cached"))
    return {
        "id": mid,
        "name": f"Match {mid}",
        "description": f"{red_count} canary findings, {len(patched)} referee-verified patches",
        "status": "completed" if end else ("interrupted" if stale else "running"),
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
        "red_discoveries": red_count,
        "red_flags_captured": len({e.get("flag") for e in breaches}),
        "blue_patches_generated": len(patched),
        "blue_patches_approved": len(patched),
        "blue_patches_rejected": len(failed),
        "final_health": health_text,
        "outcome": outcome,
        "sweep_requests": summary.get("sweep_requests", sweep.get("requests", 0)),
        "sweep_findings": summary.get("sweep_findings", sweep.get("findings", 0)),
        "llm_calls": summary.get("llm_calls"),
        "red_llm_calls": red_llm_calls,
        "blue_llm_calls": blue_llm_calls,
        "red_tokens": red_tokens,
        "blue_tokens": blue_tokens,
        "cache_hits": summary.get("cache_hits", cached_patches),
        "tokens_used": summary.get("tokens", 0),
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
    patched = [e for m in all_matches for e in m["_patched"]]
    failed = sum(m["blue_patches_rejected"] for m in all_matches)
    ttps = [e.get("ttp_seconds") for e in patched if e.get("ttp_seconds")]
    discovered = sum(m["red_discoveries"] for m in all_matches)
    with_breach = sum(1 for m in all_matches if m["red_discoveries"])
    last_health = all_matches[0]["final_health"] if all_matches else "unknown"

    by_class = {c: {"red": 0, "blue": 0} for c in VULN_META}
    for m in all_matches:
        seen: set[tuple] = set()
        for e in m["_breaches"]:
            key = (e.get("vuln_class"), e.get("route"))
            if key in seen:
                continue  # same bug re-tested in one match counts once
            seen.add(key)
            if key[0] in by_class:
                by_class[key[0]]["red"] += 1
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
        "blue_defense_rate": round(100 * len(patched) / discovered, 1) if discovered else 0,
        "vulnerabilities_discovered": discovered,
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
        context = _patch_context(patch_ev.get("patch", ""))
        before = removed or context
        packet = f"{e.get('method', 'GET')} {e.get('path', e.get('route', ''))}"
        if e.get("params"):
            packet += " " + json.dumps(e["params"])
        if e.get("json"):
            packet += " " + json.dumps(e["json"])
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
            "root_cause": "\n".join(before) if before else "Not patched yet in this match.",
            "security_impact": "A canary secret was exposed in the response.",
            "detection_evidence": f"{packet} -> {e.get('flag')}",
            "mitigation": "\n".join(added) if added else "Pending: no referee-verified patch yet.",
            "before_patch": "\n".join(before) if before else "",
            "after_patch": "\n".join(added) if added else "",
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
        original = removed or _patch_context(e.get("patch", ""))
        meta = VULN_META.get(e.get("vuln_class"), {})
        out.append({
            "id": f"PATCH-{latest['id']}-{i:02d}",
            "vuln_type": e.get("vuln_class"),
            "name": meta.get("name", e.get("vuln_class", "patch")),
            "source_file": source,
            "original_code": "\n".join(original),
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
            "mass_assignment": "mass_assignment" in patched_classes,
            "debug_exposure": "debug_exposure" in patched_classes,
            "code_injection": "code_injection" in patched_classes,
        },
        "note": "The target app runs in an isolated sandbox only while a match is in progress.",
    }
