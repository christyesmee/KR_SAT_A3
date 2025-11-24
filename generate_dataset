import os
import random

# ---------------------------------------------------------
# 1. The 4 Verified Base Puzzles (Raw Text)
# ---------------------------------------------------------
base_puzzles = {
    "easy": """0 0 0 2 6 0 7 0 1
6 8 0 0 7 0 0 9 0
1 9 0 0 0 4 5 0 0
8 2 0 1 0 0 0 4 0
0 0 4 6 0 2 9 0 0
0 5 0 0 0 3 0 2 8
0 0 9 3 0 0 0 7 4
0 4 0 0 5 0 0 3 6
7 0 3 0 1 8 0 0 0""",

    "medium": """0 2 0 6 0 8 0 0 0
5 8 0 0 0 9 7 0 0
0 0 0 0 4 0 0 0 0
3 7 0 0 0 0 5 0 0
6 0 0 0 0 0 0 0 4
0 0 8 0 0 0 0 1 3
0 0 0 0 2 0 0 0 0
0 0 9 8 0 0 0 3 6
0 0 0 3 0 6 0 9 0""",

    "hard": """0 0 0 6 0 0 4 0 0
7 0 0 0 0 3 6 0 0
0 0 0 0 9 1 0 8 0
0 0 0 0 0 0 0 0 0
0 5 0 1 8 0 0 0 3
0 0 0 3 0 6 0 4 5
0 4 0 2 0 0 0 6 0
9 0 3 0 0 0 0 0 0
0 2 0 0 0 0 1 0 0""",

    "evil": """2 0 0 3 0 0 0 0 0
8 0 4 0 6 2 0 0 3
0 1 3 8 0 0 2 0 0
0 0 0 0 2 0 3 9 0
5 0 7 0 0 0 6 2 1
0 3 2 0 0 6 0 0 0
0 2 0 0 0 9 1 4 0
6 0 1 2 5 0 8 0 9
0 0 0 0 0 1 0 0 2"""
}

# ---------------------------------------------------------
# 2. Transformation Functions (To make them unique)
# ---------------------------------------------------------
def parse_grid(text):
    """Convert string to 9x9 list of lists"""
    return [line.split() for line in text.strip().split('\n')]

def grid_to_string(grid):
    """Convert 9x9 list back to string format"""
    return '\n'.join([' '.join(row) for row in grid])

def relabel_numbers(grid):
    """Swap numbers (e.g. change all 1s to 5s, 5s to 1s)"""
    nums = list("123456789")
    shuffled = list("123456789")
    random.shuffle(shuffled)
    mapping = {n: s for n, s in zip(nums, shuffled)}
    mapping["0"] = "0" # Keep zeros as zeros
    
    new_grid = []
    for row in grid:
        new_row = [mapping[val] for val in row]
        new_grid.append(new_row)
    return new_grid

def rotate_grid(grid):
    """Rotate the board 90 degrees"""
    return list(zip(*grid[::-1]))

def reflect_grid(grid):
    """Mirror the board horizontally"""
    return [row[::-1] for row in grid]

def generate_variant(base_text):
    """Apply random transformations to create a new valid puzzle"""
    grid = parse_grid(base_text)
    
    # 1. Always Relabel (Changes the problem for the solver completely)
    grid = relabel_numbers(grid)
    
    # 2. Random Rotation
    for _ in range(random.randint(0, 3)):
        grid = rotate_grid(grid)
    
    # 3. Random Reflection
    if random.choice([True, False]):
        grid = reflect_grid(grid)
        
    return grid_to_string(grid)

# ---------------------------------------------------------
# 3. Main Generation Loop
# ---------------------------------------------------------
output_dir = "puzzles"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"📂 Generating 40 Puzzles in '{output_dir}/'...\n")

for category, raw_text in base_puzzles.items():
    print(f"🔹 Generating 10 {category.upper()} puzzles...")
    
    # Save the original as #1
    with open(f"{output_dir}/{category}_1.txt", "w") as f:
        f.write(raw_text)
        
    # Generate 9 variations
    for i in range(2, 11):
        variant = generate_variant(raw_text)
        filename = f"{output_dir}/{category}_{i}.txt"
        with open(filename, "w") as f:
            f.write(variant)

print("\n✅ DONE! You now have 40 unique puzzle files.")