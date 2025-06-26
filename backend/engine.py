import docker
import os
import shutil

UPLOAD_DIR = "uploads"
BASE_IMAGE_TAG = "edr_malware_test:latest"

client = docker.from_env()

def prepare_temp_dir(match_id, edr_script, malware_script):
    temp_dir = f"temp/{match_id}"
    os.makedirs(temp_dir, exist_ok=True)
    shutil.copy(os.path.join(UPLOAD_DIR, edr_script), os.path.join(temp_dir, "edr.py"))
    shutil.copy(os.path.join(UPLOAD_DIR, malware_script), os.path.join(temp_dir, "malware.py"))

    with open(os.path.join(temp_dir, "runner.py"), "w") as f:
        f.write("""
import subprocess
import time
import sys

print("[*] Starting EDR...")
edr = subprocess.Popen(
    ["python3", "edr.py"]
)

time.sleep(1)

print("[*] Starting Malware as 'ctf'...")
try:
    subprocess.Popen(
        ["python3", "malware.py"]
    )
except subprocess.TimeoutExpired:
    print("[!] Malware execution timeout")

try:
    edr.wait(timeout=12)
except subprocess.TimeoutExpired:
    print("[!] EDR timeout — killing...")
    edr.kill()
""")
    return temp_dir

def build_base_image():
    try:
        client.images.get(BASE_IMAGE_TAG)
    except docker.errors.ImageNotFound:
        print("[*] Building base image...")
        client.images.build(path="base_image", tag=BASE_IMAGE_TAG)

def run_docker(temp_dir, container_name):
    container = client.containers.run(
        BASE_IMAGE_TAG,
        name=container_name,
        volumes={os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'rw'}},
        working_dir="/app",
        detach=True
    )

    try:
        result = container.wait(timeout=20)
        logs = container.logs().decode(errors="ignore")
    finally:
        container.remove(force=True)

    return logs

def parse_logs(logs):
    edr_detected = "[EDR] ALERT" in logs
    malware_accessed = "[MALWARE] exfiltrated key" in logs
    return edr_detected, malware_accessed

def run_match():
    os.makedirs("temp", exist_ok=True)
    build_base_image()

    results = {
        "team1": {"edr": 0, "malware": 0, "score": 0},
        "team2": {"edr": 0, "malware": 0, "score": 0},
        "details": []
    }

    matches = [
        {
            "match_id": "team1_vs_team2",
            "edr_team": "team1",
            "malware_team": "team2",
            "edr_script": "team1_edr.py",
            "malware_script": "team2_mal.py"
        },
        {
            "match_id": "team2_vs_team1",
            "edr_team": "team2",
            "malware_team": "team1",
            "edr_script": "team2_edr.py",
            "malware_script": "team1_mal.py"
        },
    ]

    for match in matches:
        temp_dir = prepare_temp_dir(
            match["match_id"],
            match["edr_script"],
            match["malware_script"]
        )

        logs = run_docker(temp_dir, f"container_{match['match_id']}")
        print(logs)
        edr_success, malware_success = parse_logs(logs)

        results[match["edr_team"]]["edr"] += int(edr_success)
        results[match["malware_team"]]["malware"] += int(malware_success)

        results["details"].append({
            "match": match["match_id"],
            "edr_team": match["edr_team"],
            "malware_team": match["malware_team"],
            "edr_success": edr_success,
            "malware_success": malware_success,
        })

        shutil.rmtree(temp_dir)

    for team in ["team1", "team2"]:
        results[team]["score"] = results[team]["edr"] + results[team]["malware"]

    return results
