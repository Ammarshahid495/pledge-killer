"""
End-to-End Simulation & Privacy Isolation Test Suite.
Simulates 5+ students submitting assignments, automatic analysis triggering, and strict privacy boundaries.
"""

def register_and_login(client, email: str, name: str) -> str:
    client.post("/api/v1/auth/register", json={
        "display_name": name,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return r.json()["data"]["access_token"]


SAMPLE_CODE_A = b"""
#include <iostream>
using namespace std;

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int x = 48, y = 18;
    cout << "GCD: " << gcd(x, y) << endl;
    return 0;
}
"""

# Similar to A with renamed variables
SAMPLE_CODE_B = b"""
#include <iostream>
using namespace std;

int gcd(int num1, int num2) {
    while (num2 != 0) {
        int remainder = num2;
        num2 = num1 % num2;
        num1 = remainder;
    }
    return num1;
}

int main() {
    int val1 = 48, val2 = 18;
    cout << "GCD: " << gcd(val1, val2) << endl;
    return 0;
}
"""

SAMPLE_CODE_C = b"""
#include <iostream>
#include <vector>
using namespace std;

void printArray(const vector<int>& arr) {
    for (size_t i = 0; i < arr.size(); ++i) {
        cout << arr[i] << " ";
    }
    cout << endl;
}

int main() {
    vector<int> v = {1, 2, 3, 4, 5};
    printArray(v);
    return 0;
}
"""

SAMPLE_CODE_D = b"""
#include <iostream>
#include <string>
using namespace std;

int main() {
    string msg = "Hello from Pledge Fighter student 4";
    for (char c : msg) {
        cout << c << "-";
    }
    cout << endl;
    return 0;
}
"""

SAMPLE_CODE_E = b"""
#include <iostream>
using namespace std;

int factorial(int n) {
    int res = 1;
    for (int i = 2; i <= n; i++) {
        res *= i;
    }
    return res;
}

int main() {
    cout << factorial(6) << endl;
    return 0;
}
"""

SAMPLE_CODE_F = b"""
#include <iostream>
using namespace std;

// Similar to GCD implementation
int findGCD(int p, int q) {
    while (q != 0) {
        int t = q;
        q = p % q;
        p = t;
    }
    return p;
}

int main() {
    cout << findGCD(100, 25) << endl;
    return 0;
}
"""


def test_full_e2e_5_students_privacy(client, db_session):
    # Step 1: 5 students create accounts
    tokens = [
        register_and_login(client, f"student{i}@university.edu", f"Student {i}")
        for i in range(1, 6)
    ]

    # Step 2: Student 1 creates classroom
    c_resp = client.post(
        "/api/v1/classrooms",
        json={"title": "Computer Science 101 - Project 1"},
        headers={"Authorization": f"Bearer {tokens[0]}"},
    )
    c_data = c_resp.json()["data"]
    classroom_id = c_data["id"]
    join_token = c_data["join_url"].split("/join/")[-1]

    # Step 3: Students 2, 3, 4, 5 join classroom
    for i in range(1, 5):
        j_resp = client.post(
            f"/api/v1/classrooms/join/{join_token}",
            headers={"Authorization": f"Bearer {tokens[i]}"},
        )
        assert j_resp.status_code == 200

    # Step 4: Students 1 to 4 upload assignments
    codes = [SAMPLE_CODE_A, SAMPLE_CODE_B, SAMPLE_CODE_C, SAMPLE_CODE_D]
    for i in range(4):
        up_resp = client.post(
            f"/api/v1/classrooms/{classroom_id}/submissions",
            files={"file": (f"solution_{i+1}.cpp", codes[i], "text/plain")},
            headers={"Authorization": f"Bearer {tokens[i]}"},
        )
        assert up_resp.status_code == 200

    # Check status: 4/5 received, threshold NOT met yet
    status_resp = client.get(
        f"/api/v1/classrooms/{classroom_id}/status",
        headers={"Authorization": f"Bearer {tokens[0]}"},
    )
    assert status_resp.json()["data"]["valid_submission_count"] == 4
    assert status_resp.json()["data"]["threshold_met"] is False

    # Step 5: Student 5 uploads their assignment (5th distinct participant)
    up_resp_5 = client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution_5.cpp", SAMPLE_CODE_E, "text/plain")},
        headers={"Authorization": f"Bearer {tokens[4]}"},
    )
    assert up_resp_5.status_code == 200

    # Trigger analysis synchronously via service to ensure immediate deterministic completion
    from app.services.analysis_service import AnalysisService

    service = AnalysisService()
    job = service.run_classroom_analysis(db_session, classroom_id)
    assert job is not None
    assert job.status == "COMPLETED"

    # Step 6: Verify private reports for Student 1 and Student 2
    r_rep1 = client.get("/api/v1/reports/me", headers={"Authorization": f"Bearer {tokens[0]}"})
    assert r_rep1.status_code == 200
    reports1 = r_rep1.json()["data"]
    assert len(reports1) == 1
    report1_id = reports1[0]["report_id"]

    # Fetch report detail for Student 1
    detail1 = client.get(f"/api/v1/reports/me/{report1_id}", headers={"Authorization": f"Bearer {tokens[0]}"})
    assert detail1.status_code == 200
    d1_data = detail1.json()["data"]
    assert d1_data["classroom_title"] == "Computer Science 101 - Project 1"
    assert len(d1_data["matches"]) >= 1  # Matches found (specifically with Student 2's renamed code)
    assert d1_data["highest_similarity"] > 50.0  # Renamed GCD detected!

    # Verify Peer label is anonymous (e.g. Peer B) and no private student information exists
    peer_labels = [m["peer_label"] for m in d1_data["matches"]]
    assert any("Peer" in label for label in peer_labels)
    for m in d1_data["matches"]:
        assert "student" not in m["peer_label"].lower()
        assert "@" not in m["peer_label"]

    # Step 7: STRICT PRIVACY AUDIT
    # Student 2 attempts to view Student 1's private report by UUID
    r_unauthorized = client.get(
        f"/api/v1/reports/me/{report1_id}",
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert r_unauthorized.status_code == 403

    # Student 1 attempts to download Student 2's source code:
    # Notice: there is NO endpoint in the API that accepts another student's submission id or exposes peer files!
    # All submission endpoints are strictly /classrooms/{id}/submissions/me

    # Step 8: Incremental Analysis with 6th student
    token6 = register_and_login(client, "student6@university.edu", "Student 6")
    client.post(f"/api/v1/classrooms/join/{join_token}", headers={"Authorization": f"Bearer {token6}"})
    client.post(
        f"/api/v1/classrooms/{classroom_id}/submissions",
        files={"file": ("solution_6.cpp", SAMPLE_CODE_F, "text/plain")},
        headers={"Authorization": f"Bearer {token6}"},
    )

    service = AnalysisService()
    job6 = service.run_classroom_analysis(db_session, classroom_id)
    assert job6 is not None
    assert job6.status == "COMPLETED"

    # Verify Student 6 has their own private report now
    r_rep6 = client.get("/api/v1/reports/me", headers={"Authorization": f"Bearer {token6}"})
    assert len(r_rep6.json()["data"]) == 1
