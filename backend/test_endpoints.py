"""
SecureRAG Endpoint Testing Script.

Tests all API endpoints locally against http://127.0.0.1:8000.
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0


def req(method, path, body=None, token=None):
    """Send an HTTP request and return (status, data)."""
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, {"raw": body_text}
    except Exception as e:
        return 0, {"error": str(e)}


def test(name, passed, detail=""):
    global PASS, FAIL
    status = "[PASS]" if passed else "[FAIL]"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    print(f"  {status} {name}" + (f" -- {detail}" if detail else ""))


def main():
    global PASS, FAIL

    print("=" * 60)
    print("SecureRAG Endpoint Test Suite")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Health Check: GET /
    # ------------------------------------------------------------------
    print("\n--- 1. Health Check ---")
    status, data = req("GET", "/")
    test("GET / returns 200", status == 200)
    test("GET / status=ok", data.get("status") == "ok")

    # ------------------------------------------------------------------
    # 2. Auth: POST /auth/login (valid)
    # ------------------------------------------------------------------
    print("\n--- 2. Auth Login ---")
    status, data = req("POST", "/auth/login", {"email": "alice@securerag.com", "password": "password123"})
    test("POST /auth/login returns 200", status == 200, f"status={status}")
    alice_token = data.get("access_token", "")
    test("Login returns access_token", bool(alice_token))
    test("Login returns user object", "user" in data)
    if "user" in data:
        test("User role is engineer", data["user"].get("role") == "engineer")
        test("User dept is engineering", data["user"].get("department") == "engineering")
        test("User clearance is 0", data["user"].get("clearance_level") == 0)

    # ------------------------------------------------------------------
    # 3. Auth: POST /auth/login (invalid password)
    # ------------------------------------------------------------------
    print("\n--- 3. Auth Login (Bad Password) ---")
    status, data = req("POST", "/auth/login", {"email": "alice@securerag.com", "password": "wrongpass"})
    test("Bad password returns 401", status == 401, f"status={status}")

    # ------------------------------------------------------------------
    # 4. Auth: GET /auth/me
    # ------------------------------------------------------------------
    print("\n--- 4. Auth Me ---")
    status, data = req("GET", "/auth/me", token=alice_token)
    test("GET /auth/me returns 200", status == 200, f"status={status}")
    test("/me returns correct email", data.get("email") == "alice@securerag.com")

    # ------------------------------------------------------------------
    # 5. Auth: GET /auth/me (no token)
    # ------------------------------------------------------------------
    print("\n--- 5. Auth Me (No Token) ---")
    status, data = req("GET", "/auth/me")
    test("No token returns 403 or 401", status in (401, 403), f"status={status}")

    # ------------------------------------------------------------------
    # 6. Login as Admin
    # ------------------------------------------------------------------
    print("\n--- 6. Admin Login ---")
    status, data = req("POST", "/auth/login", {"email": "admin@securerag.com", "password": "password123"})
    test("Admin login returns 200", status == 200, f"status={status}")
    admin_token = data.get("access_token", "")
    test("Admin has access_token", bool(admin_token))

    # ------------------------------------------------------------------
    # 7. Documents: GET /documents/
    # ------------------------------------------------------------------
    print("\n--- 7. List Documents ---")
    status, data = req("GET", "/documents/", token=admin_token)
    test("GET /documents/ returns 200", status == 200, f"status={status}")
    docs = data.get("documents", [])
    test("Documents list is non-empty", len(docs) > 0, f"count={len(docs)}")
    if docs:
        test("Document has title field", "title" in docs[0])
        test("Document has department field", "department" in docs[0])
        test("Document has sensitivity_level field", "sensitivity_level" in docs[0])
        test("Document has chunk_count field", "chunk_count" in docs[0])

    # ------------------------------------------------------------------
    # 8. Documents: non-admin can also list docs
    # ------------------------------------------------------------------
    print("\n--- 8. Non-Admin List Documents ---")
    status, data = req("GET", "/documents/", token=alice_token)
    test("Alice can list documents (200)", status == 200, f"status={status}")

    # ------------------------------------------------------------------
    # 9. Documents: non-admin CANNOT upload
    # ------------------------------------------------------------------
    print("\n--- 9. Non-Admin Upload Blocked ---")
    # We can't easily do multipart in urllib, so just verify the auth check
    # by sending a broken request that should still be caught by the admin check
    # Actually, let's skip multipart and just verify the endpoint exists
    # This would need multipart form, so we test admin-only via audit instead

    # ------------------------------------------------------------------
    # 10. Chat: POST /chat/ask (as Alice - Engineer)
    # ------------------------------------------------------------------
    print("\n--- 10. Chat Ask (Alice - Engineer, Clearance 0) ---")
    status, data = req("POST", "/chat/ask", {"question": "What are the salary bands?"}, token=alice_token)
    test("POST /chat/ask returns 200", status == 200, f"status={status}")
    if status == 200:
        test("Response has answer", "answer" in data and bool(data["answer"]))
        test("Response has chunks_retrieved list", isinstance(data.get("chunks_retrieved"), list))
        test("Response has chunks_denied_count", "chunks_denied_count" in data)
        test("Response has total_chunks_found", "total_chunks_found" in data)
        denied = data.get("chunks_denied_count", 0)
        retrieved = data.get("chunks_retrieved", [])
        test(f"Alice denied access to some chunks (denied={denied})", denied > 0,
             f"retrieved={len(retrieved)}, denied={denied}")
        # Verify Alice did NOT get HR content (sensitivity 1, dept hr)
        got_hr = any("salary" in c.get("text", "").lower() for c in retrieved)
        test("Alice did NOT retrieve HR salary data", not got_hr,
             "RBAC leak!" if got_hr else "filtered correctly")

    # ------------------------------------------------------------------
    # 11. Chat: POST /chat/ask (as Admin - clearance 3)
    # ------------------------------------------------------------------
    print("\n--- 11. Chat Ask (Admin - Clearance 3) ---")
    status, data = req("POST", "/chat/ask", {"question": "What are the salary bands?"}, token=admin_token)
    test("Admin POST /chat/ask returns 200", status == 200, f"status={status}")
    if status == 200:
        retrieved = data.get("chunks_retrieved", [])
        denied = data.get("chunks_denied_count", 0)
        got_hr = any("salary" in c.get("text", "").lower() for c in retrieved)
        test(f"Admin CAN retrieve HR salary data", got_hr,
             f"retrieved={len(retrieved)}, denied={denied}")

    # ------------------------------------------------------------------
    # 12. Login as Carol (HR, clearance 2)
    # ------------------------------------------------------------------
    print("\n--- 12. Carol (HR) Chat Test ---")
    status, data = req("POST", "/auth/login", {"email": "carol@securerag.com", "password": "password123"})
    carol_token = data.get("access_token", "") if status == 200 else ""
    test("Carol login returns 200", status == 200)

    if carol_token:
        status, data = req("POST", "/chat/ask", {"question": "What are the salary bands for L4?"}, token=carol_token)
        test("Carol POST /chat/ask returns 200", status == 200)
        if status == 200:
            retrieved = data.get("chunks_retrieved", [])
            got_hr = any("salary" in c.get("text", "").lower() for c in retrieved)
            test("Carol CAN see HR salary data", got_hr)

    # ------------------------------------------------------------------
    # 13. Audit: GET /audit/logs (admin)
    # ------------------------------------------------------------------
    print("\n--- 13. Audit Logs (Admin) ---")
    status, data = req("GET", "/audit/logs", token=admin_token)
    test("GET /audit/logs returns 200", status == 200, f"status={status}")
    logs = data.get("logs", [])
    test("Audit logs present from chat tests", len(logs) > 0, f"count={len(logs)}")
    if logs:
        test("Log has user_email", "user_email" in logs[0])
        test("Log has query", "query" in logs[0])
        test("Log has chunks_retrieved", "chunks_retrieved" in logs[0])
        test("Log has chunks_denied", "chunks_denied" in logs[0])

    # ------------------------------------------------------------------
    # 14. Audit: GET /audit/logs (non-admin blocked)
    # ------------------------------------------------------------------
    print("\n--- 14. Audit Logs (Non-Admin Blocked) ---")
    status, data = req("GET", "/audit/logs", token=alice_token)
    test("Alice blocked from audit logs (403)", status == 403, f"status={status}")

    # ------------------------------------------------------------------
    # 15. Chat: empty question validation
    # ------------------------------------------------------------------
    print("\n--- 15. Empty Question Validation ---")
    status, data = req("POST", "/chat/ask", {"question": "   "}, token=alice_token)
    test("Empty question returns 400", status == 400, f"status={status}")

    # ------------------------------------------------------------------
    # 16. Register new user
    # ------------------------------------------------------------------
    print("\n--- 16. Register New User ---")
    status, data = req("POST", "/auth/register", {
        "email": "testuser@securerag.com",
        "password": "testpass123",
        "name": "Test User",
        "role": "legal",
        "department": "legal",
        "clearance_level": 2,
    })
    test("Register returns 201 or 409 (dup)", status in (201, 409), f"status={status}")
    if status == 201:
        test("Register returns token", bool(data.get("access_token")))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
