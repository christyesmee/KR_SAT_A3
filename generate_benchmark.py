#!/usr/bin/env python3
"""
Non-Consecutive Sudoku benchmark puzzle generator.
2 modes - txt and sat - differ not only in the output format, but also on the algorithm for generating UNSAT puzzles (the harder part of the problem)
txt -> build an unsat by merging two sats, non=deterministcally look for one. It's working for SAT puzzles, as well as for UNSAT 9x9 puzzles, but does not work (or works, but extremally slow) for UNSAT 16s and forth.
cnf -> build a puzzle with no clues, but modify the rules to include a deep, nontrivial contradiction (nb. this kind of puzzle is impossible to write down in sudoku (txt) format!). 
This approach for UNSAt is fast and scalable - recommended for generating large unsat puzzles.

The generator uses Glucose 4.2.1; a SOTA SAT solver. It requires you have Glucose binary installed/built, and requests a path to Glucose as an argument.
The generator saves puzzles matching the treshold values of conflicts or time (per size x type). For your use, feel free to adjust(first lines after the imports).

Note: -1 conflicts is Glucose timeout code - if you see it, especially when generating 25 SAT puzzles, consider increasing the timeout (one of this function flags/params).
"""

import argparse, csv, datetime, math, os, random, re, subprocess, sys, tempfile, time
from pathlib import Path
from typing import Iterable, List, Tuple, Dict, Any, Optional

THRESHOLDS = {
    9: {
        "sat":   {"min_conf": 5,  "min_time": 0.1},
        "unsat": {"min_conf": 2,  "min_time": 0.05},
    },
    16: {
        "sat":   {"min_conf": 50, "min_time": 1.00},
        "unsat": {"min_conf": 1,  "min_time": 0.1},
    },
    25: {
        "sat":   {"min_conf": 100, "min_time": 3},
        "unsat": {"min_conf": 1, "min_time": 1},
    },
}

def logmsg(logf, msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    sys.stdout.flush()
    if logf:
        logf.write(line + "\n")
        logf.flush()

def var_id(r: int, c: int, v: int, n: int) -> int:
    return r * n * n + c * n + v

def exactly_one(lits: Iterable[int]) -> List[List[int]]:
    lits = list(lits)
    cls = [lits]
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            cls.append([-lits[i], -lits[j]])
    return cls

def orthogonal_neighbors(r: int, c: int, n: int):
    if r > 0: yield r - 1, c
    if r + 1 < n: yield r + 1, c
    if c > 0: yield r, c - 1
    if c + 1 < n: yield r, c + 1

#encoder
def encode_nonconsecutive_to_cnf(grid: List[List[int]]) -> Tuple[List[List[int]], int]:
    n = len(grid)
    b = int(math.isqrt(n))
    num_vars = n ** 3 
    cls: List[List[int]] = []

    #cell constraints
    for r in range(n):
        for c in range(n):
            cls.extend(exactly_one(var_id(r, c, v, n) for v in range(1, n + 1)))

    #row / column / block constraints
    for v in range(1, n + 1):
        #rows
        for r in range(n):
            cls.extend(exactly_one(var_id(r, cc, v, n) for cc in range(n)))
        #cols
        for c in range(n):
            cls.extend(exactly_one(var_id(rr, c, v, n) for rr in range(n)))
        #blocks
        for br in range(0, n, b):
            for bc in range(0, n, b):
                cells = [(br+i, bc+j) for i in range(b) for j in range(b)]
                cls.extend(exactly_one(var_id(rr, cc, v, n) for rr, cc in cells))

    #non-consecutive rule
    for r in range(n):
        for c in range(n):
            for v in range(1, n+1):
                for rr, cc in orthogonal_neighbors(r, c, n):
                    if v+1 <= n:
                        cls.append([-var_id(r,c,v,n), -var_id(rr,cc,v+1,n)])
                    if v-1 >= 1:
                        cls.append([-var_id(r,c,v,n), -var_id(rr,cc,v-1,n)])

    # clues
    for r in range(n):
        for c in range(n):
            v = grid[r][c]
            if v:
                cls.append([var_id(r,c,v,n)])

    return cls, num_vars


def write_dimacs(cls: List[List[int]], num_vars: int, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"p cnf {num_vars} {len(cls)}\n")
        for cl in cls:
            f.write(" ".join(str(x) for x in cl) + " 0\n")

def write_grid(grid: List[List[int]], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for row in grid:
            f.write(" ".join(map(str, row)) + "\n")

def _build_standard_sudoku(n: int) -> List[List[int]]:
    b = int(math.isqrt(n))
    def pattern(r,c): return (b*(r%b) + r//b + c) % n
    base = list(range(1,n+1))
    grid = [[base[pattern(r,c)] for c in range(n)] for r in range(n)]

    def shuffle_blocks(seq):
        blocks=[seq[i:i+b] for i in range(0,n,b)]
        random.shuffle(blocks)
        return [x for block in blocks for x in block]

    rows = shuffle_blocks(list(range(n)))
    cols = shuffle_blocks(list(range(n)))
    return [[grid[r][c] for c in cols] for r in rows]

def _count_nc_violations(grid):
    n=len(grid)
    bad=0
    for r in range(n):
        for c in range(n):
            for rr,cc in orthogonal_neighbors(r,c,n):
                if (rr,cc)>(r,c) and abs(grid[r][c]-grid[rr][cc])==1:
                    bad+=1
    return bad

def _try_nc_mapping(grid, tries_map=1000):
    n=len(grid)
    digs=list(range(1,n+1))
    for _ in range(tries_map):
        mapping=dict(zip(digs,random.sample(digs,n)))
        cand=[[mapping[v] for v in row] for row in grid]
        if _count_nc_violations(cand)==0:
            return cand
    return None

def generate_full_nc(n, log=None, ignore_cache=False):
    cache=Path("benchmarks/cache")
    cache.mkdir(parents=True,exist_ok=True)
    cp=cache/f"full_{n}.txt"

    if not ignore_cache and cp.exists():
        logmsg(log,f"[cache] Loading cached {n}x{n}")
        return [[int(x) for x in l.split()] for l in cp.read_text().splitlines()]

    logmsg(log,f"[{n}] generating full NC Sudoku...")
    for _ in range(300):
        base=_build_standard_sudoku(n)
        mapped=_try_nc_mapping(base)
        if mapped:
            with open(cp,"w") as f:
                for row in mapped: f.write(" ".join(map(str,row))+"\n")
            return mapped
    raise RuntimeError("No NC grid")

def make_sat_puzzle(sol, ratio):
    n=len(sol)
    grid=[r[:] for r in sol]
    cells=[(r,c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    target=int(n*n*ratio)
    for r,c in cells[target:]: grid[r][c]=0
    return grid

def _null_sink():
    return "NUL" if os.name=="nt" else "/dev/null"

_CONF_RE=re.compile(r"(?:conflicts|Conflicts)\s*[:=]\s*([0-9]+)")
_RES_RE=re.compile(r"s\s+(SATISFIABLE|UNSATISFIABLE)", re.I)

def parse_solver_output(out):
    m=_RES_RE.search(out)
    if m:
        r=m.group(1).upper()
        result="UNSAT" if "UNSAT" in r else "SAT"
    else:
        U=out.upper()
        if "UNSATISFIABLE" in U: result="UNSAT"
        elif "SATISFIABLE" in U: result="SAT"
        else: result="UNKNOWN"

    c=_CONF_RE.search(out)
    return {"result":result, "conflicts": int(c.group(1)) if c else -1}

def run_solver(solver, cnf, timeout):
    t0=time.time()
    try:
        p=subprocess.run([solver,str(cnf),_null_sink()],
                         capture_output=True,text=True,timeout=timeout)
        d=parse_solver_output(p.stdout+p.stderr)
        d["time"]=time.time()-t0
        return d
    except subprocess.TimeoutExpired:
        return {"result":"TIMEOUT","conflicts":-1,"time":timeout}

def encode_to_tempfile(grid):
    cls,nv=encode_nonconsecutive_to_cnf(grid)
    tmp=Path(tempfile.mktemp(suffix=".cnf"))
    write_dimacs(cls,nv,tmp)
    return tmp,nv,len(cls)

def build_merged_from_two(p1,p2):
    n=len(p1)
    out=[[0]*n for _ in range(n)]
    cells=[(r,c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    for r,c in cells:
        out[r][c]=p1[r][c] or p2[r][c]
    return out

def nonzero_cells(grid):
    n=len(grid)
    return [(r,c) for r in range(n) for c in range(n) if grid[r][c]!=0]

def random_prune_until_unsat(n, base, solver, timeout, min_conf, min_time, ratios, log):
    digs=list(range(1,n+1))
    perm=random.sample(digs,n)
    mapping={d:perm[d-1] for d in digs}
    full2=[[mapping[v] for v in row] for row in base]

    MAX_OUTER=10
    MAX_PRUNE=100

    for ratio in ratios:
        for _ in range(MAX_OUTER):
            p1=make_sat_puzzle(base,ratio)
            p2=make_sat_puzzle(full2,ratio)
            merged=build_merged_from_two(p1,p2)

            for _ in range(MAX_PRUNE):
                tmp,_,_=encode_to_tempfile(merged)
                res=run_solver(solver,tmp,timeout)
                tmp.unlink(missing_ok=True)

                if res["result"]=="UNSAT":
                    hard=(res["conflicts"]>=min_conf) or (res["time"]>=min_time)
                    if hard:
                        logmsg(log,f"[{n} UNSAT r={ratio}] conf={res['conflicts']} t={res['time']:.3f}")
                        return merged
                    nz=nonzero_cells(merged)
                    if not nz: break
                    r,c=random.choice(nz)
                    merged[r][c]=0

                elif res["result"]=="SAT":
                    nz=nonzero_cells(merged)
                    if not nz: break
                    r,c=random.choice(nz)
                    merged[r][c]=0

        logmsg(log,f"[{n}] switch ratio r={ratio}")

    raise RuntimeError("No hard UNSAT")

#unsat for cnf mode - insert nontrivial rule violation, leave w/o clues
def build_structured_unsat_cnf(n: int) -> Tuple[List[List[int]], int]:

    grid = [[0]*n for _ in range(n)]
    cls, nv = encode_nonconsecutive_to_cnf(grid)

    r = random.randint(0, n-1)
    c = random.randint(0, n-1)
    neigh = list(orthogonal_neighbors(r, c, n))
    (rr, cc) = random.choice(neigh)

    v = random.randint(2, n-1)

    def X(a,b,val):
        return var_id(a,b,val,n)

    A1 = nv + 1
    A2 = nv + 2
    A3 = nv + 3
    A4 = nv + 4
    nv = nv + 4

    cls.append([-A1, X(r,c,v)])
    cls.append([-A1, X(rr,cc,v+1)])

    cls.append([-A2, X(r,c,v+1)])
    cls.append([-A2, X(rr,cc,v)])

    cls.append([-A3, X(r,c,v)])
    cls.append([-A3, X(rr,cc,v-1)])

    cls.append([-A4, X(r,c,v-1)])
    cls.append([-A4, X(rr,cc,v)])

    cls.append([A1, A2, A3, A4])
    
    pairs=[(A1,A2),(A1,A3),(A1,A4),(A2,A3),(A2,A4),(A3,A4)]
    for x,y in pairs:
        cls.append([-x,-y])

    return cls, nv

CSV_FIELDS=["size","type","index","conflicts","time_sec","result","file"]

def csv_writer_for(folder):
    p=folder/"results.csv"
    exists=p.exists()
    f=open(p,"a",encoding="utf-8",newline="")
    w=csv.DictWriter(f,fieldnames=CSV_FIELDS)
    if not exists: w.writeheader()
    w._f=f
    return w

def csv_close(w): w._f.close()


### global manifest
def manifest_writer(root: Path):
    p = root / "manifest.csv"
    exists = p.exists()
    f = open(p, "a", encoding="utf-8", newline="")
    w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    if not exists:
        w.writeheader()
    w._f = f
    return w

def manifest_close(w):
    w._f.close()



def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--glucose",required=True)
    ap.add_argument("--out",default="benchmark_puzzles")
    ap.add_argument("--num",type=int,default=5)
    ap.add_argument("--quick-timeout",type=int,default=30)
    ap.add_argument("--mode",choices=["txt","cnf"],default="txt")
    ap.add_argument("--ratios",type=str,
        default="0.45, 0.5, 0.4, 0.3, 0.35, 0.2, 0.65, 0.25, 0.15, 0.6")
    args=ap.parse_args()

    ratios=[float(x) for x in args.ratios.split(",") if x.strip()]
    sizes=[9,16,25]

    root=Path(args.out)
    root.mkdir(exist_ok=True)
    logp=root/"benchmark.log"

    manifest = manifest_writer(root)

    with open(logp,"w") as log:
        for n in sizes:
            logmsg(log,f"=== SIZE {n} ===")
            base=generate_full_nc(n,log)

            sat_dir=root/f"{n}_sat"; sat_dir.mkdir(exist_ok=True)
            unsat_dir=root/f"{n}_unsat"; unsat_dir.mkdir(exist_ok=True)
            sat_csv=csv_writer_for(sat_dir)
            unsat_csv=csv_writer_for(unsat_dir)

            SAT_CONF=THRESHOLDS[n]["sat"]["min_conf"]
            SAT_TIME=THRESHOLDS[n]["sat"]["min_time"]
            UNSAT_CONF=THRESHOLDS[n]["unsat"]["min_conf"]
            UNSAT_TIME=THRESHOLDS[n]["unsat"]["min_time"]

            created=0
            while created<args.num:
                selected=None
                sel_ratio=None

                for ratio in ratios:
                    cand=make_sat_puzzle(base,ratio)
                    tmp,_,_=encode_to_tempfile(cand)
                    res=run_solver(args.glucose,tmp,args.quick_timeout)
                    tmp.unlink(missing_ok=True)

                    hard=(res["conflicts"]>=SAT_CONF) or (res["time"]>=SAT_TIME)
                    logmsg(log,f"[{n} sat-test r={ratio:.2f}] conf={res['conflicts']} t={res['time']:.2f}")

                    if res["result"]=="SAT" and hard:
                        selected=cand
                        sel_ratio=ratio
                        break

                if selected is None:
                    selected=cand
                    sel_ratio=ratio
                    logmsg(log,f"[{n}] SAT fallback r={ratio:.2f}")

                tmp,_,_=encode_to_tempfile(selected)
                resf=run_solver(args.glucose,tmp,args.quick_timeout)
                tmp.unlink(missing_ok=True)

                hard=(resf["conflicts"]>=SAT_CONF) or (resf["time"]>=SAT_TIME)

                if resf["result"]=="SAT" and hard:
                    if args.mode=="txt":
                        f=sat_dir/f"sat_{created:03}.txt"
                        write_grid(selected,f)
                    else:
                        f=sat_dir/f"sat_{created:03}.cnf"
                        cls2,nv2=encode_nonconsecutive_to_cnf(selected)
                        write_dimacs(cls2,nv2,f)

                    row = {
                        "size":n,"type":"sat","index":created,
                        "conflicts":resf["conflicts"],
                        "time_sec":f"{resf['time']:.2f}",
                        "result":"SAT","file":str(f)
                    }

                    sat_csv.writerow(row)
                    manifest.writerow(row)
                    sat_csv._f.flush()
                    manifest._f.flush()

                    logmsg(log,f"[{n} sat] {f.name}: conf={resf['conflicts']} t={resf['time']:.2f}")
                    created+=1
                else:
                    logmsg(log,f"[{n} sat] discard r={sel_ratio:.2f}")

            if args.mode=="txt":
                created=0
                while created<args.num:
                    try:
                        puz=random_prune_until_unsat(
                            n,base,args.glucose,args.quick_timeout,
                            UNSAT_CONF,UNSAT_TIME,ratios,log
                        )
                    except RuntimeError:
                        logmsg(log,f"[{n} unsat] FAILED")
                        break

                    cls3,nv3=encode_nonconsecutive_to_cnf(puz)
                    tmp=Path(tempfile.mktemp(suffix=".cnf"))
                    write_dimacs(cls3,nv3,tmp)
                    resu=run_solver(args.glucose,tmp,args.quick_timeout)
                    tmp.unlink(missing_ok=True)

                    hard=(resu["conflicts"]>=UNSAT_CONF) or (resu["time"]>=UNSAT_TIME)

                    if resu["result"]=="UNSAT" and hard:
                        f=unsat_dir/f"unsat_{created:03}.txt"
                        write_grid(puz,f)

                        row = {
                            "size":n,"type":"unsat","index":created,
                            "conflicts":resu["conflicts"],
                            "time_sec":f"{resu['time']:.2f}",
                            "result":"UNSAT","file":str(f)
                        }

                        unsat_csv.writerow(row)
                        manifest.writerow(row)
                        unsat_csv._f.flush()
                        manifest._f.flush()

                        logmsg(log,f"[{n} unsat] {f.name}: conf={resu['conflicts']} t={resu['time']:.2f}")
                        created+=1
                    else:
                        logmsg(log,f"[{n} unsat] discard trivial")

            else:
                created=0
                while created<args.num:
                    cls_uns, nv_uns = build_structured_unsat_cnf(n)
                    f=unsat_dir/f"unsat_{created:03}.cnf"
                    write_dimacs(cls_uns, nv_uns, f)

                    resu = run_solver(args.glucose, f, args.quick_timeout)

                    row = {
                        "size":n,"type":"unsat","index":created,
                        "conflicts":resu["conflicts"],
                        "time_sec":f"{resu['time']:.2f}",
                        "result":"UNSAT",
                        "file":str(f)
                    }

                    unsat_csv.writerow(row)
                    manifest.writerow(row)
                    unsat_csv._f.flush()
                    manifest._f.flush()

                    logmsg(log,f"[{n} unsat-cnf] {f.name}: conf={resu['conflicts']} t={resu['time']:.2f}")
                    created+=1

            csv_close(sat_csv)
            csv_close(unsat_csv)

    manifest_close(manifest)

if __name__=="__main__":
    main()
