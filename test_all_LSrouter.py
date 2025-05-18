import subprocess

# Danh sách file test của bạn
json_files = [
    "01_small_net.json",
    "02_small_net_events.json",
    "03_pg244_net.json",
    "04_pg244_net_events.json",
    "05_pg242_net.json",
    "06_pg242_net_events.json"
]

def run_test(filename):
    print(f"\nRunning test on {filename}...")
    result = subprocess.run(
        ["python", "network.py", filename, "LS"],
        capture_output=True,
        text=True
    )
    
    if "SUCCESS: All Routes correct!" in result.stdout:
        print(f"{filename}: PASS")
    else:
        print(f"{filename}: FAIL")
        print(result.stdout)

if __name__ == "__main__":
    for file in json_files:
        run_test(file)
