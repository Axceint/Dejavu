"""API smoke test. Run from repo root: .venv\\Scripts\\python -m tests.test_api"""
import io
import time
import zipfile

from fastapi.testclient import TestClient

from dejavu.api import app

c = TestClient(app)


def wait(job_id):
    for _ in range(1200):
        s = c.get(f"/api/scans/{job_id}").json()
        if s["state"] != "running":
            return s
        time.sleep(0.05)
    raise AssertionError("scan did not finish in 60 s")


def zipped(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, src in files.items():
            z.writestr(n, src)
    return buf.getvalue()


# demo: same ranking the Streamlit app shows, plus both exports
jid = c.post("/api/scans/demo").json()["id"]
assert wait(jid)["state"] == "done"
data = c.get(f"/api/scans/{jid}/result").json()
kind = lambda i: data["files"][i]["name"].split("/")[1].split(".")[0]
assert all({kind(p["a"]), kind(p["b"])} == {"orig", "ai_rewrite"} for p in data["pairs"][:6])
csv = c.get(f"/api/scans/{jid}/pairs.csv")
assert csv.headers["content-type"].startswith("text/csv") and csv.text.startswith("rank,score,file_a,file_b")
page = c.get(f"/api/scans/{jid}/report.html", params={"theme": '"; alert(1); "'}).text
assert "const DATA = {" in page and "const HOST_THEME = null;" in page

# upload with starter code: the shared template stops counting
template = "def solve(grid):\n    seen = set()\n    for row in grid:\n        for cell in row:\n            if cell not in seen:\n                seen.add(cell)\n    return len(seen)\n"
a = template + "print(solve([[1, 2], [3, 1]]))\n"
b = template + "x = [[5]]\nprint(solve(x) * 2)\n"
sub = ("class.zip", zipped({"a.py": a, "b.py": b}), "application/zip")
jid = c.post("/api/scans", files={"submissions": sub}).json()["id"]
assert wait(jid)["state"] == "done"
assert c.get(f"/api/scans/{jid}/result").json()["pairs"][0]["score"] > 0.4
jid = c.post("/api/scans", files={"submissions": sub, "starter": ("starter.py", template.encode())}).json()["id"]
assert wait(jid)["state"] == "done"
scores = [p["score"] for p in c.get(f"/api/scans/{jid}/result").json()["pairs"]]
assert all(s < 0.2 for s in scores), scores

# errors: broken zip, wrong starter type, unknown or unfinished scan
bad = wait(c.post("/api/scans", files={"submissions": ("x.zip", b"not a zip")}).json()["id"])
assert bad["state"] == "error" and bad["error"].startswith("Couldn't scan x.zip"), bad
r = c.post("/api/scans", files={"submissions": sub, "starter": ("..", b"x")})
assert r.status_code == 400, r.text
assert c.get("/api/scans/nope").status_code == 404
assert c.get("/api/scans/nope/result").status_code == 404
print("API PASS")
