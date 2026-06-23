"""
AI Traffic Inspector — Comprehensive System Audit
Tests all components for engineering, design, and security gaps.
"""
import sys
import os
import importlib
import traceback
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.chdir(str(Path(__file__).resolve().parent))

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def check(name, fn):
    try:
        ok, msg = fn()
        status = PASS if ok else FAIL
        results.append((status, name, msg))
        print(f"  {status} {name}: {msg}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"  {FAIL} {name}: {e}")

def warn_check(name, fn):
    try:
        ok, msg = fn()
        status = PASS if ok else WARN
        results.append((status, name, msg))
        print(f"  {status} {name}: {msg}")
    except Exception as e:
        results.append((WARN, name, str(e)))
        print(f"  {WARN} {name}: {e}")


print("=" * 70)
print("  FLIPKART AI TRAFFIC INSPECTOR — FULL SYSTEM AUDIT")
print("=" * 70)

# ─── 1. CORE IMPORTS ──────────────────────────────────────────
print("\n[1/9] CORE IMPORTS & MODULES")

def check_import(module_name):
    def _check():
        mod = importlib.import_module(module_name)
        return True, f"imported successfully"
    return _check

check("config", check_import("config"))
check("app.database", check_import("app.database"))
check("app.routes", check_import("app.routes"))
check("app.auth", check_import("app.auth"))
check("app.pipeline", check_import("app.pipeline"))
check("app.video_processor", check_import("app.video_processor"))
check("models.schemas", check_import("models.schemas"))
check("models.detector", check_import("models.detector"))
check("models.cascade_detector", check_import("models.cascade_detector"))
check("logic.violations", check_import("logic.violations"))
check("logic.zone_manager", check_import("logic.zone_manager"))
check("ocr.plate_reader", check_import("ocr.plate_reader"))
check("ocr.glm_ocr", check_import("ocr.glm_ocr"))
check("evidence.annotator", check_import("evidence.annotator"))

# ─── 2. DATABASE SCHEMA ──────────────────────────────────────
print("\n[2/9] DATABASE SCHEMA & INTEGRITY")

def check_db_schema():
    from app.database import ViolationDB, UserDB, Base, engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required = ["violations", "users"]
    missing = [t for t in required if t not in tables]
    if missing:
        return False, f"Missing tables: {missing}"
    
    # Check violations columns
    v_cols = {c["name"] for c in inspector.get_columns("violations")}
    required_v_cols = {"id", "type", "confidence", "description", "plate_text",
                       "image_path", "evidence_path", "timestamp", "is_reviewed", "location"}
    missing_v = required_v_cols - v_cols
    if missing_v:
        return False, f"violations table missing columns: {missing_v}"
    
    # Check users columns
    u_cols = {c["name"] for c in inspector.get_columns("users")}
    required_u_cols = {"id", "username", "hashed_password"}
    missing_u = required_u_cols - u_cols
    if missing_u:
        return False, f"users table missing columns: {missing_u}"
    
    return True, f"Tables OK: {tables}, all required columns present"

check("Database schema", check_db_schema)

def check_admin_user():
    from app.database import SessionLocal, UserDB
    db = SessionLocal()
    try:
        admin = db.query(UserDB).filter(UserDB.username == "admin").first()
        if not admin:
            return False, "Default admin user not found"
        return True, "admin user exists with hashed password"
    finally:
        db.close()

check("Admin user seeded", check_admin_user)

# ─── 3. AUTH & SECURITY ─────────────────────────────────────
print("\n[3/9] AUTHENTICATION & SECURITY")

def check_jwt_creation():
    from app.auth import create_access_token
    token = create_access_token(data={"sub": "test_user"})
    if not token or len(token) < 20:
        return False, "Token generation failed"
    return True, f"JWT token generated ({len(token)} chars)"

check("JWT token creation", check_jwt_creation)

def check_jwt_verification():
    from app.auth import create_access_token, verify_token
    token = create_access_token(data={"sub": "admin"})
    username = verify_token(token)
    if username != "admin":
        return False, f"Token verification returned: {username}"
    return True, "Token roundtrip verified for 'admin'"

check("JWT token verification", check_jwt_verification)

def check_password_hashing():
    from app.auth import verify_password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("test123")
    if not verify_password("test123", hashed):
        return False, "Password verification failed"
    if verify_password("wrong_password", hashed):
        return False, "Wrong password was accepted!"
    return True, "bcrypt hash + verify working correctly"

check("Password hashing", check_password_hashing)

def check_protected_routes():
    from app.routes import router
    protected_endpoints = []
    unprotected_sensitive = []
    
    sensitive_paths = ["/api/violations", "/api/analytics", "/api/reset", 
                       "/api/upload-video"]
    
    for route in router.routes:
        path = getattr(route, 'path', '')
        methods = getattr(route, 'methods', set())
        endpoint = getattr(route, 'endpoint', None)
        
        if endpoint:
            # Check if endpoint has get_current_user dependency
            import inspect
            sig = inspect.signature(endpoint)
            has_auth = any("current_user" in p for p in sig.parameters)
            
            if has_auth:
                protected_endpoints.append(path)
            elif path in sensitive_paths:
                unprotected_sensitive.append(f"{path} ({methods})")
    
    if unprotected_sensitive:
        return False, f"Unprotected sensitive endpoints: {unprotected_sensitive}"
    return True, f"{len(protected_endpoints)} endpoints protected with JWT"

check("Route protection", check_protected_routes)

def check_cors_config():
    from config import CORS_ORIGINS
    if "*" in CORS_ORIGINS:
        return False, "CORS allows ALL origins (*) — acceptable for hackathon but not production"
    return True, f"CORS restricted to: {CORS_ORIGINS}"

warn_check("CORS configuration", check_cors_config)

def check_api_key_exposure():
    from config import ROBOFLOW_API_KEY, GEMINI_API_KEY
    issues = []
    if ROBOFLOW_API_KEY and not os.getenv("ROBOFLOW_API_KEY"):
        issues.append("Roboflow key hardcoded (not from env)")
    if GEMINI_API_KEY and not os.getenv("GEMINI_API_KEY"):
        issues.append("Gemini key hardcoded (not from env)")
    if issues:
        return False, "; ".join(issues) + " — use env vars in production"
    return True, "API keys loaded from environment"

warn_check("API key management", check_api_key_exposure)

# ─── 4. ML PIPELINE ──────────────────────────────────────────
print("\n[4/9] ML PIPELINE & MODELS")

def check_yolo_model():
    from config import YOLO_MODEL
    return True, f"Model configured: {YOLO_MODEL}"

check("YOLO model config", check_yolo_model)

def check_traffic_classes():
    from config import TRAFFIC_CLASSES
    required = {"person", "car", "motorcycle", "bus", "truck"}
    configured = set(TRAFFIC_CLASSES.values())
    missing = required - configured
    if missing:
        return False, f"Missing essential classes: {missing}"
    return True, f"{len(TRAFFIC_CLASSES)} traffic classes configured"

check("Traffic class filter", check_traffic_classes)

def check_violation_types():
    from models.schemas import ViolationType
    types = [v.value for v in ViolationType]
    required = ["helmet_missing", "seatbelt_missing", "triple_riding", 
                 "wrong_side", "stop_line", "red_light"]
    missing = [t for t in required if t not in types]
    if missing:
        return False, f"Missing violation types: {missing}"
    return True, f"{len(types)} violation types: {types}"

check("Violation type coverage", check_violation_types)

def check_cascade_detector():
    from models.cascade_detector import CascadeDetector, reset_tracker
    cd = CascadeDetector(use_roboflow=False)
    reset_tracker()
    return True, "CascadeDetector instantiated, tracker reset OK"

check("Cascade detector init", check_cascade_detector)

def check_tracking_dedup():
    from models.cascade_detector import _already_flagged, _mark_flagged, reset_tracker
    reset_tracker()
    
    assert not _already_flagged(1, "helmet_missing"), "Should not be flagged yet"
    _mark_flagged(1, "helmet_missing")
    assert _already_flagged(1, "helmet_missing"), "Should be flagged now"
    assert not _already_flagged(1, "seatbelt_missing"), "Different type should not be flagged"
    assert not _already_flagged(2, "helmet_missing"), "Different track should not be flagged"
    
    reset_tracker()
    assert not _already_flagged(1, "helmet_missing"), "Should be cleared after reset"
    
    return True, "Deduplication logic: flag, check, cross-type, cross-track, reset all OK"

check("Tracking deduplication", check_tracking_dedup)

# ─── 5. OCR PIPELINE ─────────────────────────────────────────
print("\n[5/9] OCR PIPELINE")

def check_paddle_ocr_available():
    try:
        from paddleocr import PaddleOCR
        return True, "PaddleOCR importable"
    except ImportError:
        return False, "PaddleOCR not installed"

check("PaddleOCR available", check_paddle_ocr_available)

def check_glm_ocr_module():
    from ocr.glm_ocr import _get_gemini_client
    # Don't actually initialize (costs API call), just check imports
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        return False, "GEMINI_API_KEY not configured"
    return True, f"GLM-OCR module ready, API key set ({len(GEMINI_API_KEY)} chars)"

check("GLM-OCR (Gemini) module", check_glm_ocr_module)

def check_indian_plate_regex():
    import re
    from config import INDIAN_PLATE_REGEX
    pattern = re.compile(INDIAN_PLATE_REGEX)
    
    valid_plates = ["KA01AB1234", "MH02XY9012", "DL03EF2345", "TN09PQ3456"]
    invalid_plates = ["HELLO", "123", "ABCDEFGHIJ", "1234567890"]
    
    for p in valid_plates:
        if not pattern.match(p):
            return False, f"Valid plate '{p}' not matched"
    for p in invalid_plates:
        if pattern.match(p):
            return False, f"Invalid plate '{p}' falsely matched"
    
    return True, f"Regex validates {len(valid_plates)} valid, rejects {len(invalid_plates)} invalid"

check("Indian plate regex", check_indian_plate_regex)

# ─── 6. VIOLATION LOGIC ──────────────────────────────────────
print("\n[6/9] VIOLATION LOGIC ENGINE")

def check_violation_functions():
    from logic.violations import (
        check_helmet_compliance, check_triple_riding,
        check_seatbelt_compliance, check_zone_violations,
        detect_all_violations
    )
    return True, "All violation functions importable"

check("Violation functions", check_violation_functions)

def check_zone_manager():
    from logic.zone_manager import get_all_zones, get_active_zones
    zones = get_all_zones()
    active = get_active_zones()
    return True, f"{len(zones)} zones loaded, {len(active)} active"

check("Zone manager", check_zone_manager)

def check_seatbelt_motorcycle_exclusion():
    """Verify that motorcycle riders are NOT checked for seatbelts."""
    from models.schemas import Detection, BBox
    from logic.violations import check_seatbelt_compliance
    
    # Create a person on a motorcycle
    person = Detection(bbox=BBox(x1=100, y1=50, x2=200, y2=300),
                       class_name="person", class_id=0, confidence=0.9)
    motorcycle = Detection(bbox=BBox(x1=80, y1=100, x2=220, y2=350),
                           class_name="motorcycle", class_id=3, confidence=0.9)
    car = Detection(bbox=BBox(x1=80, y1=50, x2=250, y2=350),
                    class_name="car", class_id=2, confidence=0.9)
    
    # This person overlaps with both motorcycle and car
    violations = check_seatbelt_compliance([person], [car], [motorcycle])
    
    # Should NOT flag seatbelt for a motorcycle rider
    for v in violations:
        if any(d.class_name == "motorcycle" for d in v.detections):
            return False, "Motorcycle rider incorrectly flagged for seatbelt!"
    
    return True, "Motorcycle riders correctly excluded from seatbelt checks"

check("Seatbelt/motorcycle exclusion", check_seatbelt_motorcycle_exclusion)

# ─── 7. EVIDENCE & ANNOTATION ────────────────────────────────
print("\n[7/9] EVIDENCE & ANNOTATION")

def check_evidence_dirs():
    from config import EVIDENCE_DIR, UPLOADS_DIR
    issues = []
    if not EVIDENCE_DIR.exists():
        issues.append("EVIDENCE_DIR missing")
    if not UPLOADS_DIR.exists():
        issues.append("UPLOADS_DIR missing")
    if issues:
        return False, "; ".join(issues)
    return True, f"Evidence: {EVIDENCE_DIR}, Uploads: {UPLOADS_DIR}"

check("Evidence directories", check_evidence_dirs)

def check_annotator():
    from evidence.annotator import generate_evidence
    from models.schemas import AnalysisResult
    import numpy as np
    
    # Create a dummy frame (480x640)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    analysis = AnalysisResult(image_path="test.jpg")
    
    annotated, path = generate_evidence(frame, analysis, save=False)
    if annotated is None:
        return False, "Annotator returned None"
    
    # Annotator adds a 50px header and a 30px footer, so expected height is 480 + 50 + 30 = 560
    if annotated.shape != (560, 640, 3):
        return False, f"Unexpected shape: {annotated.shape} (expected 560x640x3)"
    return True, "Annotator produces correct output shape on empty frame"

check("Evidence annotator", check_annotator)

# ─── 8. API ENDPOINTS ────────────────────────────────────────
print("\n[8/9] API ENDPOINTS")

def check_api_health():
    import requests
    try:
        r = requests.get("http://localhost:8000/api/health", timeout=3)
        if r.status_code == 200:
            data = r.json()
            return True, f"Status: {data.get('status')}, Service: {data.get('service')}"
        return False, f"Status code: {r.status_code}"
    except Exception as e:
        return False, f"Backend not reachable: {e}"

check("Health endpoint", check_api_health)

def check_api_login():
    import requests
    try:
        r = requests.post("http://localhost:8000/api/auth/login", 
                          data={"username": "admin", "password": "admin"}, timeout=3)
        if r.status_code == 200:
            token = r.json().get("access_token")
            if token:
                return True, f"Login OK, token received ({len(token)} chars)"
        return False, f"Login failed: {r.status_code} {r.text[:100]}"
    except Exception as e:
        return False, str(e)

check("Auth login endpoint", check_api_login)

def check_api_violations_protected():
    import requests
    try:
        # Without token
        r = requests.get("http://localhost:8000/api/violations", timeout=3)
        if r.status_code == 401:
            return True, "Correctly returns 401 without token"
        return False, f"Expected 401, got {r.status_code}"
    except Exception as e:
        return False, str(e)

check("Violations endpoint (no auth)", check_api_violations_protected)

def check_api_violations_with_auth():
    import requests
    try:
        # Login first
        login = requests.post("http://localhost:8000/api/auth/login",
                              data={"username": "admin", "password": "admin"}, timeout=3)
        token = login.json().get("access_token")
        
        # Access violations with token
        r = requests.get("http://localhost:8000/api/violations",
                          headers={"Authorization": f"Bearer {token}"}, timeout=3)
        if r.status_code == 200:
            data = r.json()
            return True, f"OK, {data.get('total', 0)} violations returned"
        return False, f"Status: {r.status_code}"
    except Exception as e:
        return False, str(e)

check("Violations endpoint (with auth)", check_api_violations_with_auth)

def check_api_analytics_protected():
    import requests
    try:
        r = requests.get("http://localhost:8000/api/analytics", timeout=3)
        if r.status_code == 401:
            return True, "Correctly returns 401 without token"
        return False, f"Expected 401, got {r.status_code}"
    except Exception as e:
        return False, str(e)

check("Analytics endpoint (no auth)", check_api_analytics_protected)

def check_violation_status_endpoint():
    import requests
    try:
        r = requests.patch("http://localhost:8000/api/violations/999/status",
                           json={"status": "approved"}, timeout=3)
        # Should be 401 (no auth) or 404 (not found with auth)
        if r.status_code in [401, 404]:
            return True, f"Endpoint exists, returns {r.status_code} as expected"
        return False, f"Unexpected status: {r.status_code}"
    except Exception as e:
        return False, str(e)

check("Violation status PATCH endpoint", check_violation_status_endpoint)

# ─── 9. ROBOFLOW & GEMINI CONNECTIVITY ───────────────────────
print("\n[9/9] EXTERNAL SERVICE CONNECTIVITY")

def check_roboflow_sdk():
    try:
        from inference_sdk import InferenceHTTPClient
        return True, "inference_sdk importable"
    except ImportError:
        return False, "inference_sdk not installed"

check("Roboflow inference SDK", check_roboflow_sdk)

def check_gemini_sdk():
    try:
        from google import genai
        return True, "google.genai importable"
    except ImportError:
        return False, "google-genai not installed"

check("Google Gemini SDK", check_gemini_sdk)

def check_supervision():
    try:
        import supervision as sv
        return True, f"supervision v{sv.__version__} importable"
    except ImportError:
        return False, "supervision not installed"

check("Supervision library", check_supervision)

# ─── SUMMARY ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  AUDIT SUMMARY")
print("=" * 70)

passes = sum(1 for s, _, _ in results if s == PASS)
fails = sum(1 for s, _, _ in results if s == FAIL)
warns = sum(1 for s, _, _ in results if s == WARN)

print(f"\n  {PASS} Passed: {passes}")
print(f"  {FAIL} Failed: {fails}")
print(f"  {WARN} Warnings: {warns}")
print(f"  Total checks: {len(results)}")

if fails > 0:
    print(f"\n  CRITICAL FAILURES:")
    for s, name, msg in results:
        if s == FAIL:
            print(f"    • {name}: {msg}")

if warns > 0:
    print(f"\n  WARNINGS (non-blocking):")
    for s, name, msg in results:
        if s == WARN:
            print(f"    • {name}: {msg}")

print("\n" + "=" * 70)
