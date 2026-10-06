import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_department_portals():
    print("Testing Department Web Portals...")

    # 1. Surveillance Dashboard
    r_dash = client.get("/dashboard")
    assert r_dash.status_code == 200, f"Dashboard failed: {r_dash.status_code}"
    assert "AcciSense" in r_dash.text
    assert "/ws/alerts" in r_dash.text
    assert "/api/accidents" in r_dash.text
    print("✅ 1. Central Surveillance Dashboard (/dashboard) OK")

    # 2. Hospital ER Portal
    r_hosp = client.get("/hospital")
    assert r_hosp.status_code == 200, f"Hospital portal failed: {r_hosp.status_code}"
    assert "Hospital Emergency & ER Trauma Center" in r_hosp.text
    assert "/ws/alerts" in r_hosp.text
    assert "HOSPITAL_NOTIFIED" in r_hosp.text
    print("✅ 2. Hospital ER Portal (/hospital) OK")

    # 3. Police Traffic Portal
    r_pol = client.get("/police")
    assert r_pol.status_code == 200, f"Police portal failed: {r_pol.status_code}"
    assert "Police Department Traffic Control Station" in r_pol.text
    assert "/ws/alerts" in r_pol.text
    assert "POLICE_NOTIFIED" in r_pol.text
    print("✅ 3. Police Traffic Portal (/police) OK")

    # 4. Ambulance EMS Portal
    r_amb = client.get("/ambulance")
    assert r_amb.status_code == 200, f"Ambulance portal failed: {r_amb.status_code}"
    assert "Ambulance & EMS Emergency Rescue Station" in r_amb.text
    assert "/ws/alerts" in r_amb.text
    assert "AMBULANCE_EN_ROUTE" in r_amb.text
    print("✅ 4. Ambulance EMS Portal (/ambulance) OK")


def run_all_phase5_tests():
    print("==================================================")
    print("RUNNING PHASE 5 DEPARTMENT PORTALS TESTS")
    print("==================================================")
    test_department_portals()
    print("==================================================")
    print("ALL PHASE 5 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_all_phase5_tests()
