import os, time, subprocess, glob

PUZZLE_DIR = "puzzles"
TIMEOUT = 5

files = sorted(glob.glob(os.path.join(PUZZLE_DIR, "*.txt")))
print(f"Found {len(files)} puzzles. Running benchmark...")

with open("results.csv", "w") as f:
    f.write("Category,Puzzle,Time,Backtracks,Status\n")
    for filepath in files:
        filename = os.path.basename(filepath)
        if "easy" in filename: cat = "Easy"
        elif "medium" in filename: cat = "Medium"
        elif "hard" in filename: cat = "Hard"
        else: cat = "Evil"
        
        print(f"Running {filename}...", end=" ", flush=True)
        start = time.time()
        try:
            # Assuming your main.py takes --in
            result = subprocess.run(["python", "main.py", "--in", filepath], capture_output=True, text=True, timeout=TIMEOUT)
            duration = time.time() - start
            
            # Parse backtracks if present
            bt = "0"
            if "Backtracks=" in result.stdout:
                bt = result.stdout.split("Backtracks=")[1].split()[0]
            
            status = "SAT" if "SAT" in result.stdout else "UNSAT"
            print(f"{status} in {duration:.2f}s")
            f.write(f"{cat},{filename},{duration:.4f},{bt},{status}\n")
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            f.write(f"{cat},{filename},{TIMEOUT},TIMEOUT,TIMEOUT\n")