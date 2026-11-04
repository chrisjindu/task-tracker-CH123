"""healthcheck.py: check Task Tracker, compare its version, and save a JSON report."""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
 
import requests
import yaml
 
 
def load_config(path):
    """Read the YAML configuration file and return it as a dictionary."""
    with open(path) as file:
        return yaml.safe_load(file)
 
 
def classify(status_code):
    """Turn an HTTP status code into UP, ERROR, or DOWN."""
    if status_code is None:
        return "DOWN"
    if 200 <= status_code < 300:
        return "UP"
    return "ERROR"
 
 
def version_matches(actual, expected):
    """Return True when no version is expected, or when the versions are equal."""
    return expected is None or actual == expected
 
 
def check(url, timeout):
    """Call one health URL and return the result as a dictionary."""
    try:
        response = requests.get(url, timeout=timeout)
        version = response.json().get("version", "unknown")
        return {"url": url, "status_code": response.status_code, "version": version}
    except requests.exceptions.RequestException as error:
        return {"url": url, "status_code": None, "error": type(error).__name__}
 
 
def tool_version():
    """Return the short Git commit ID of this repository, or 'unknown'."""
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"
 
 
def main():
    parser = argparse.ArgumentParser(description="Check the health of Task Tracker.")
    parser.add_argument("--config", default="config.yaml", help="YAML settings file")
    parser.add_argument("--output", default="reports/health.json", help="report file")
    parser.add_argument("--expect-version", help="version that should be running")
    args = parser.parse_args()
 
    config = load_config(args.config)
    results = []
    for target in config["targets"]:
        result = check(target["url"], config["timeout_seconds"])
        result["name"] = target["name"]
        result["state"] = classify(result["status_code"])
        if result["state"] == "UP" and not version_matches(
            result.get("version"), args.expect_version
        ):
            result["state"] = "WRONG VERSION"
        results.append(result)
        print(f"{result['name']:<20} {result['state']:<14} {result.get('version', '-')}")
 
    report = {
        "owner": config["owner"],
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": tool_version(),
        "expected_version": args.expect_version,
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(f"Report saved to {output}")
 
    if any(result["state"] != "UP" for result in results):
        raise SystemExit(1)
 
 
if __name__ == "__main__":
    main()

