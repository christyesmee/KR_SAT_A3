import os
import subprocess
import csv
import sys
import time

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = os.path.join("NCSudoku_benchmark_set", "compact_sudokus")

# List the files you want to test
FILES_TO_TEST = [
    # "easy.txt",
    # "medium.txt",
     "hard.txt",
    #"all_9x9.txt"
]

OUTPUT_CSV = "results_compact.csv"
TEMP_FILE = "temp_current_puzzle.txt"
TIMEOUT_SECS = 120 
# ==========================================

def count_givens(puzzle_string):
    """Counts non-empty cells (digits 1-9) in the string"""
    count = 0
    for char in puzzle_string:
        if char.isdigit() and char != '0':
            count += 1
    return count

def run_tests():
    print(f"🚀 Starting Benchmark (Clean Output)")
    print(f"📂 Output: {OUTPUT_CSV}")
    print("-" * 50)

    with open(OUTPUT_CSV, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Source_File", "Puzzle_ID", "Givens", "InitProps", "Time", "Result", "Backtracks"])

        for filename in FILES_TO_TEST:
            source_path = os.path.join(BASE_DIR, filename)

            if not os.path.exists(source_path):
                print(f"⚠️  Skipping: {filename} (File not found)")
                continue

            print(f"\n🔹 Processing File: {filename}")

            try:
                with open(source_path, "r") as f:
                    lines = [l.strip() for l in f if l.strip()]
            except Exception as e:
                print(f"❌ Error reading file: {e}")
                continue

            print(f"   Found {len(lines)} puzzles.")

            for i, puzzle_line in enumerate(lines):
                puzzle_id = i + 1
                num_givens = count_givens(puzzle_line)

                # Write single puzzle to temp file
                with open(TEMP_FILE, "w") as tf:
                    tf.write(puzzle_line)

                start_time = time.time()
                process = subprocess.Popen(
                    ["python", "main.py", "--in", TEMP_FILE, "--standard-only"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                final_output = ""
                timed_out = False
                
                try:
                    while process.poll() is None:
                        elapsed = int(time.time() - start_time)
                        if elapsed > TIMEOUT_SECS:
                            process.kill()
                            timed_out = True
                            raise subprocess.TimeoutExpired(process.args, TIMEOUT_SECS)
                        
                        print(f"\r   🧩 #{puzzle_id} (Givens: {num_givens}): {elapsed}/{TIMEOUT_SECS}s", end="", flush=True)
                        time.sleep(0.1)

                    stdout, _ = process.communicate()
                    final_output = stdout.strip()
                    duration = time.time() - start_time

                except subprocess.TimeoutExpired:
                    duration = TIMEOUT_SECS
                    print(f"\r   🧩 #{puzzle_id} (Givens: {num_givens}): TIMEOUT!        ", end="", flush=True)
                
                # --- PARSING LOGIC (FIXED) ---
                p_res = "UNKNOWN"
                p_bt = "0"
                p_props = "0"
                
                if timed_out:
                    p_res = "TIMEOUT"
                    p_bt = "TIMEOUT"
                    p_props = "TIMEOUT"
                elif "[PUZZLE]" in final_output:
                    try:
                        parts = final_output.split("|")
                        for part in parts:
                            if "Result:" in part: 
                                p_res = part.split(":")[1].strip()
                            if "Backtracks:" in part: 
                                p_bt = part.split(":")[1].strip()
                            if "InitProps:" in part: 
                                # THE FIX: Take only the first word to avoid trailing junk
                                raw_prop = part.split(":")[1].strip()
                                p_props = raw_prop.split()[0] 
                    except: pass

                # Save
                writer.writerow([filename, puzzle_id, num_givens, p_props, f"{duration:.4f}", p_res, p_bt])
                csv_file.flush()
                
                if not timed_out:
                    print(f"\r   🧩 #{puzzle_id} (Givens: {num_givens} | Props: {p_props}): {duration:.2f}s | {p_res} | BT: {p_bt}   ")
                else:
                    print("") 

    if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
    print("-" * 50)
    print(f"🎉 Done.")

if __name__ == "__main__":
    run_tests()