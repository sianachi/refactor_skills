"""Grade optimize runs: python3 scripts/grade_optimize.py <iteration-dir> [case ...]

Per run: the project's own checks, then the case's hidden/check.sh (correctness and cost, never shown to the
agent). Assertions 4 and 5 (tests added, report contents) are judged by a reader and come from manual.json
next to grading.json: {"3": [true, "evidence"], "4": [true, "evidence"]}.
"""
import json, os, re, subprocess, sys

EVALS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimize", "evals")
VISIBLE = {
    "go": "go build ./... && go vet ./... && echo CHECKS-OK",
    "csharp": "dotnet build $(find src -name '*.csproj' -not -path '*/obj/*' | head -1) -v q 2>&1 | tail -3 | grep -q ' 0 Error' && echo CHECKS-OK",
    "ts": "(npm ci --silent --prefer-offline >/dev/null 2>&1 || true) && npm run typecheck --silent && npm run build --silent >/dev/null && echo CHECKS-OK",
}
CORRECTNESS = re.compile(r"differ|count text|options|steps|build failed|load failed|run failed|did not start")


def sh(cmd, cwd, timeout=3600):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


it = os.path.abspath(sys.argv[1])
only = set(sys.argv[2:])
for case in sorted(os.listdir(it)):
    if not os.path.isdir(f"{EVALS}/{case}") or (only and case not in only):
        continue
    meta = json.load(open(f"{it}/{case}/eval_metadata.json"))
    for cfg in sorted(os.listdir(f"{it}/{case}")):
        if os.environ.get("GRADE_CONFIGS") and cfg not in os.environ["GRADE_CONFIGS"].split(","):
            continue
        run = f"{it}/{case}/{cfg}"
        repo = f"{run}/outputs/repo"
        if not os.path.isdir(repo):
            continue
        lang = case.split("-")[0]
        if os.environ.get("REUSE") and os.path.exists(f"{run}/hidden-check.txt"):  # re-score saved output
            vis, hid = "CHECKS-OK" if json.load(open(f"{run}/grading.json"))["expectations"][0]["passed"] else "", open(f"{run}/hidden-check.txt").read()
        else:
            _, vis = sh(VISIBLE[lang], repo)
            rc, hid = sh(f"bash {EVALS}/{case}/hidden/check.sh {repo}", repo)
        fails = [l for l in hid.splitlines() if ":" in l and not l.count("|")]
        corr = [l for l in fails if CORRECTNESS.search(l)]
        cost = [l for l in fails if l not in corr]
        ok = "hidden: all checks pass" in hid
        manual = json.load(open(f"{run}/manual.json")) if os.path.exists(f"{run}/manual.json") else {}
        auto = [
            ("CHECKS-OK" in vis, vis[-300:]),
            (ok or (not corr and "|200|" in hid), "\n".join(corr) or ("all responses identical" if "|200|" in hid else hid[-400:])),
            (ok or not cost, "\n".join(cost) or "all cost limits met"),
        ]
        exps = []
        for i, text in enumerate(meta["assertions"]):
            passed, ev = auto[i] if i < 3 else manual.get(str(i), [False, "not graded yet"])
            exps.append({"text": text, "passed": bool(passed), "evidence": str(ev)})
        n = sum(e["passed"] for e in exps)
        json.dump({"expectations": exps, "summary": {"passed": n, "failed": len(exps) - n, "total": len(exps), "pass_rate": round(n / len(exps), 2)}},
                  open(f"{run}/grading.json", "w"), indent=2)
        open(f"{run}/hidden-check.txt", "w").write(hid)
        print(f"{case:38} {cfg:14} {n}/{len(exps)}  checks={'ok' if auto[0][0] else 'FAIL'} correct={'ok' if auto[1][0] else 'FAIL'} cost={'ok' if auto[2][0] else 'FAIL'}")
        for l in fails[:12]:
            print("    " + l)
