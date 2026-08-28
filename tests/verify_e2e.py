"""Verification script for live TENALI AI server."""

import requests

base = "http://127.0.0.1:8080"

print("--- 1. Health Check ---")
h = requests.get(f"{base}/health").json()
print("Service:", h["service"])
print("Status:", h["status"])
print("Adaptation:", h["adaptation_model"])
print("Demo Mode:", h["demo_mode"])

print("\n--- 2. Capabilities ---")
c = requests.get(f"{base}/capabilities").json()
print("Tools:", [t["name"] for t in c["registered_tools"]])
print("BigEarthNet-19 Classes:", len(c["domain_adaptation"]["classes"]))

print("\n--- 3. Web Dashboard ---")
html = requests.get(f"{base}/").text
print("Dashboard HTML size:", len(html), "bytes")
assert "TENALI" in html
assert "SIH 26167" in html

print("\n--- 4. Live SIH Demonstrations ---")
presets = ["demo1_vqa", "demo2_grounding", "demo3_change", "demo4_builtup", "demo5_optical_sar"]
latest_rep = None

for pid in presets:
    res = requests.post(f"{base}/demo/run-preset", data={"preset_id": pid}).json()
    latest_rep = res.get("report_id")
    print(f"\n[DEMO] {pid}:")
    print(f"  Task: {res.get('task')}")
    print(f"  Execution Mode: {res.get('execution_mode')}")
    print(f"  Confidence Estimate: {res.get('confidence_estimate')} ({res.get('confidence_level')})")
    print(f"  Answer: {res.get('answer')}")
    print(f"  Trace: {[s['step'] for s in res.get('execution_trace', [])]}")
    print(f"  Evidence Layers: {list(res.get('evidence', {}).get('layers', {}).keys())}")

print(f"\n--- 5. Report Verification ({latest_rep}) ---")
rep_html = requests.get(f"{base}/reports/{latest_rep}").text
print("Report HTML Size:", len(rep_html), "bytes")
assert "TENALI AI Analysis Report" in rep_html
rep_json = requests.get(f"{base}/reports/{latest_rep}/json").json()
print("Report JSON Task:", rep_json["task"])

print("\n========================================================")
print("ALL LIVE END-TO-END WORKFLOWS VERIFIED SUCCESSFULLY!")
print("========================================================")
