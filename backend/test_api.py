"""VibeSport API - Integration test script."""
import requests

BASE = "http://localhost:8000/api"
passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name} -> {e}")
        failed += 1


print("=" * 50)
print("VibeSport API CRUD Integration Tests")
print("=" * 50)

# 1. Health
test("Health check", lambda: requests.get(f"{BASE}/health").raise_for_status())

# 2. Auth flow — use a new unique user each time
import uuid
uid = str(uuid.uuid4())[:8]
email = f"test-{uid}@vibesport.com"
password = "test12345"
token = None

r = requests.post(f"{BASE}/auth/register", json={"username": f"testuser-{uid}", "email": email, "password": password})
r.raise_for_status()
token = r.json()["access_token"]
print(f"    registered: {r.json()['username']}")
headers = {"Authorization": f"Bearer {token}"}

# 3. Profile
test("GET /auth/me", lambda: (
    r := requests.get(f"{BASE}/auth/me", headers=headers), r.raise_for_status()
))

# 4. Running CRUD
run_id = None
test("POST /running", lambda: (
    r := requests.post(f"{BASE}/running", headers=headers, json={"distance_km": 5.2, "log_date": "2026-07-17", "notes": "Morning run"}),
    r.raise_for_status(),
    (id_ := r.json()["log_id"], globals().__setitem__("run_id", id_))
))

test("GET /running", lambda: (
    r := requests.get(f"{BASE}/running", headers=headers), r.raise_for_status()
))

test("GET /running/stats", lambda: (
    r := requests.get(f"{BASE}/running/stats", params={"period": "week"}, headers=headers),
    r.raise_for_status(),
    print(f" [{r.json()['total_km']}km, {r.json()['count']} runs]")
))

test("PATCH /running/{id}", lambda: (
    r := requests.patch(f"{BASE}/running/{run_id}", headers=headers, json={"distance_km": 6.0}),
    r.raise_for_status()
))

# 5. Fitness
fit_id = None
test("POST /fitness", lambda: (
    r := requests.post(f"{BASE}/fitness", headers=headers, json={"exercise_type": "Squat", "reps_sets": "4x12", "log_date": "2026-07-17"}),
    r.raise_for_status(),
    globals().__setitem__("fit_id", r.json()["fitness_id"])
))

test("GET /fitness/stats", lambda: (
    r := requests.get(f"{BASE}/fitness/stats", params={"period": "week"}, headers=headers),
    r.raise_for_status(),
    print(f" [{r.json()['total_sessions']} sessions]")
))

# 6. Weight
wt_id = None
test("POST /weight", lambda: (
    r := requests.post(f"{BASE}/weight", headers=headers, json={"weight_value": 72.5, "unit": "kg", "log_date": "2026-07-17"}),
    r.raise_for_status(),
    globals().__setitem__("wt_id", r.json()["weight_id"])
))

test("GET /weight/stats", lambda: (
    r := requests.get(f"{BASE}/weight/stats", headers=headers), r.raise_for_status()
))

test("GET /weight/trend", lambda: (
    r := requests.get(f"{BASE}/weight/trend", params={"days": 7}, headers=headers),
    r.raise_for_status()
))

# 7. Dashboard
test("GET /dashboard", lambda: (
    r := requests.get(f"{BASE}/dashboard", headers=headers),
    r.raise_for_status(),
    print(f" {r.json()}")
))

# 8. Exercise types
test("GET /exercise-types (15 presets)", lambda: (
    r := requests.get(f"{BASE}/exercise-types"), r.raise_for_status()
))

# 9. Validation
test("POST /running (future date) -> 422", lambda: (
    r := requests.post(f"{BASE}/running", headers=headers, json={"distance_km": 5.0, "log_date": "2099-01-01"}),
    None if r.status_code == 422 else (_ for _ in ()).throw(AssertionError(f"expected 422, got {r.status_code}"))
))

test("POST /running (km > 100) -> 422", lambda: (
    r := requests.post(f"{BASE}/running", headers=headers, json={"distance_km": 999, "log_date": "2026-07-17"}),
    None if r.status_code == 422 else (_ for _ in ()).throw(AssertionError(f"expected 422, got {r.status_code}"))
))

# 10. Profile update
test("PATCH /auth/me", lambda: (
    r := requests.patch(f"{BASE}/auth/me", headers=headers, json={"target_weight_kg": 65.0}),
    r.raise_for_status()
))

# 11. Cleanup
test("DELETE /running/{id}", lambda: requests.delete(f"{BASE}/running/{run_id}", headers=headers).raise_for_status())
test("DELETE /fitness/{id}", lambda: requests.delete(f"{BASE}/fitness/{fit_id}", headers=headers).raise_for_status())
test("DELETE /weight/{id}", lambda: requests.delete(f"{BASE}/weight/{wt_id}", headers=headers).raise_for_status())

# 12. Auth guards
test("GET /dashboard (no token) -> 403", lambda: (
    r := requests.get(f"{BASE}/dashboard"),
    None if r.status_code == 403 else (_ for _ in ()).throw(AssertionError(f"expected 403, got {r.status_code}"))
))

test("POST /auth/login (wrong pwd) -> 401", lambda: (
    r := requests.post(f"{BASE}/auth/login", json={"email": email, "password": "wrong"}),
    None if r.status_code == 401 else (_ for _ in ()).throw(AssertionError(f"expected 401, got {r.status_code}"))
))

print("=" * 50)
print(f"Results: {passed} passed, {failed} failed ({passed + failed} total)")
print("=" * 50)
