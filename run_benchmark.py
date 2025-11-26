import os
import time
import subprocess
import csv


dir = "NCSudoku_benchmark_set" 
puzzle_dirs = [
                 ""
            #    "test_sat",
            #    "9_sat", 
            #    "9_unsat", 
            #    "16_sat", 
            #    "25_sat"
                   ] 
output = "benchmark_results.csv"

timout_secs = 120

def run_tests():
    print(f"starting tests | timeout = {timout_secs} seconds")
    print("-" * 50)

    with open(output, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["folder", "puzzle", "time (s)", "result", "backtracks"])

        #loop through each folder
        for folder in puzzle_dirs:
            folder_path = os.path.join(dir, folder)
            
            if not os.path.exists(folder_path):
                print(f"{folder} (folder not found)")
                continue

            print(f"\n Processing: {folder}")
            
            # Get files and sort them so they run in order (01, 02, 03...)
            files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
            files.sort()

            # Run on the first 10 puzzles of each folder to be safe/fast
            # Remove [:10] if you want to run ALL of them.
            for filename in files[:10]:
                full_path = os.path.join(folder_path, filename)
                print(f"   Running {filename}...", end=" ", flush=True)

                start_time = time.time()
                try:
                    # Execute your main.py using subprocess
                    result = subprocess.run(
                        ["python", "main.py", "--in", full_path],
                        capture_output=True,
                        text=True,
                        timeout=timout_secs
                    )
                    duration = time.time() - start_time
                    
                    # Parse the output from solver.py
                    # Expected format from print: "[STANDARD] Result: SAT | Backtracks: 50"
                    output_text = result.stdout.strip()
                    
                    # Default values in case parsing fails
                    status = "UNKNOWN"
                    backtracks = "0"
                    
                    if "Result:" in output_text:
                        # Extract SAT/UNSAT
                        status = "SAT" if "SAT" in output_text else "UNSAT"
                    
                    if "Backtracks:" in output_text:
                        # Extract number after "Backtracks:"
                        parts = output_text.split("Backtracks:")
                        if len(parts) > 1:
                            backtracks = parts[1].strip()

                    print(f"✅ {duration:.2f}s | {status} | BT: {backtracks}")
                    
                    # Save to CSV
                    writer.writerow([folder, filename, f"{duration:.4f}", status, backtracks])

                except subprocess.TimeoutExpired:
                    print("❌ TIMEOUT")
                    writer.writerow([folder, filename, "TIMEOUT", "TIMEOUT", "TIMEOUT"])
                except Exception as e:
                    print(f"❌ ERROR: {e}")

    print("-" * 50)
    print("🎉 Benchmark Complete. Check 'benchmark_results.csv'.")

if __name__ == "__main__":
    run_tests()