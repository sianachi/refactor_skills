"""Grade debloat runs: python3 grade.py <iteration-dir>.

Per run: visible checks, hidden contract tests (never shown to the agent), and source size.
Writes grading.json (+ loc.json) per run and prints a table.
"""
import json, os, re, shutil, subprocess, sys, tempfile

EVALS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "debloat", "evals")
EXT = (".py", ".js", ".go", ".cs")

# case -> (visible check cmd, hidden setup fn, hidden cmd, original LOC computed at run time, target reduction)
TARGET = {  # fraction of original source lines the run must cut, set from the best result seen so far
    "python-inventory-keeps-dynamic-handlers": 0.55,
    "node-lib-keeps-public-exports": 0.40,
    "go-cli-no-tests-stays-cautious": 0.55,
    "python-orders-enterprise-layers": 0.72,
    "csharp-api-keeps-reflection-and-json": 0.50,
}


def sh(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=180)
    return p.returncode, (p.stdout + p.stderr).strip()


def loc(root):
    n = 0
    for dp, dns, fs in os.walk(root):
        dns[:] = [d for d in dns if d not in (".git", "tests", "test", "__pycache__", "node_modules", "bin", "obj")]
        for f in fs:
            if f.endswith(EXT) and not f.endswith("_test.go"):
                n += sum(1 for line in open(os.path.join(dp, f)) if line.strip())
    return n


def checks(case, repo):
    hidden = os.path.join(EVALS, case, "hidden")
    tmp = tempfile.mkdtemp()
    try:
        shutil.copytree(repo, tmp, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "bin", "obj"))
        if case.startswith("python"):
            vis = sh("python3 -m unittest 2>&1 | tail -1", tmp)
            os.makedirs(f"{tmp}/tests", exist_ok=True)
            open(f"{tmp}/tests/__init__.py", "a").close()
            shutil.copy(f"{hidden}/test_hidden_contract.py", f"{tmp}/tests/")
            hid = sh("python3 -m unittest tests.test_hidden_contract 2>&1 | tail -15", tmp)
            return (vis[1].endswith("OK"), vis[1]), (hid[1].endswith("OK"), hid[1][-600:])
        if case.startswith("node"):
            vis = sh("node --test 2>&1 | grep -E '^. (pass|fail) '", tmp)
            os.makedirs(f"{tmp}/test", exist_ok=True)
            shutil.copy(f"{hidden}/hidden-contract.test.js", f"{tmp}/test/")
            hid = sh("node --test test/hidden-contract.test.js 2>&1 | grep -E '^. (pass|fail) |not ok|expected|actual' | head -20", tmp)
            return ("fail 0" in vis[1], vis[1]), ("fail 0" in hid[1], hid[1][-600:])
        if case.startswith("csharp"):
            vis = sh("dotnet build $(find . -name '*.csproj' -not -path '*/obj/*' | head -1) -v q 2>&1 | tail -3", tmp)
            hid = sh(f"bash {hidden}/check.sh {tmp}", tmp)
            return (re.search(r"\b0 Error\(s\)", vis[1]) is not None, vis[1][-300:]), (hid[0] == 0, hid[1][-800:])
        if case.startswith("go"):
            vis = sh("go build -o tc . && go vet ./... && echo built", tmp)
            hid = sh(f"bash {hidden}/check.sh ./tc", tmp)
            return (vis[1].endswith("built"), vis[1][-300:]), (hid[0] == 0, hid[1][-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def report_ok(run):
    r = open(f"{run}/outputs/report.md").read().lower() if os.path.exists(f"{run}/outputs/report.md") else ""
    ok = ("removed" in r or "deleted" in r) and any(k in r for k in ("left in place", "kept", "not removed", "left alone"))
    return ok, "report has removed and kept sections" if ok else "report missing removed/kept sections"


it = sys.argv[1]
rows = []
for case in sorted(os.listdir(it)):
    if not os.path.isdir(f"{it}/{case}") or case not in TARGET:
        continue
    before = loc(f"{EVALS}/{case}/files")
    for cfg in sorted(os.listdir(f"{it}/{case}")):
        run = f"{it}/{case}/{cfg}"
        if not os.path.isdir(f"{run}/outputs/repo"):
            continue
        after = loc(f"{run}/outputs/repo")
        cut = 1 - after / before
        (vp, ve), (hp, he) = checks(case, f"{run}/outputs/repo")
        rp, re_ = report_ok(run)
        t = TARGET[case]
        exps = [
            {"text": "The project's own checks pass on the final code (tests, or build and vet)", "passed": vp, "evidence": ve},
            {"text": "Hidden contract tests pass: public behavior, outputs, errors and messages are unchanged", "passed": hp, "evidence": he},
            {"text": f"Source shrank by at least {int(t*100)}% (non-blank lines outside tests)", "passed": cut >= t, "evidence": f"{before} -> {after} lines ({cut:.0%} cut)"},
            {"text": "The report lists what was removed and what was left in place", "passed": rp, "evidence": re_},
        ]
        n = sum(e["passed"] for e in exps)
        json.dump({"expectations": exps, "summary": {"passed": n, "failed": 4 - n, "total": 4, "pass_rate": n / 4}}, open(f"{run}/grading.json", "w"), indent=2)
        json.dump({"before": before, "after": after, "cut": round(cut, 3), "hidden_pass": hp}, open(f"{run}/loc.json", "w"))
        rows.append((case, cfg, before, after, cut, vp, hp, n))
print(f"{'case':42} {'config':14} {'lines':>11} {'cut':>5} vis hid score")
for c, cfg, b, a, cut, vp, hp, n in rows:
    print(f"{c:42} {cfg:14} {b:4} -> {a:4} {cut:5.0%} {'ok' if vp else 'XX':>3} {'ok' if hp else 'XX':>3} {n}/4")
