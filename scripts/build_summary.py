"""Build summary.js, the numbers the results page shows, from data/results.csv.

Run from the repository root:  python3 scripts/build_summary.py

Every figure on the page comes from this file, so the page and the CSV cannot
disagree. Rules:

- A task that cannot pass in these sandboxes even with its reference fix
  (passable = 0) is left out everywhere.
- The four-agent comparison uses only the tasks graded in every run, so
  every agent's totals cover the same tasks.
- The Agency and Pi comparison, attempt by attempt, uses the tasks both were
  graded on in that attempt.
- A trial that failed on the sandbox side has no row in the CSV.
"""

import csv
import json
import math
import statistics

AGENTS = [
    {
        "key": "agency",
        "name": "Agency",
        "runs": [
            "k1-agency-minimal",
            "k2-agency-minimal",
            "k3-agency-minimal",
            "k4-agency-minimal",
            "k5-agency-minimal",
        ],
        "when": "five runs, 13 to 15 Nov 2026",
    },
    {
        "key": "pi",
        "name": "Pi 1.5.2",
        "runs": ["k1-pi", "k2-pi", "k3-pi", "k4-pi", "k5-pi"],
        "when": "five runs, 13 to 15 Nov 2026",
    },
    {
        "key": "opencode",
        "name": "OpenCode 1.19.5",
        "runs": ["ref-opencode"],
        "when": "one run, 11 Nov 2026",
    },
    {
        "key": "mini",
        "name": "mini-SWE-agent 2.4.6",
        "runs": ["ref-mini"],
        "when": "one run, 13 Nov 2026",
    },
]
PAIR = ["agency", "pi"]


def sign_test(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def totals(run_rows, tasks):
    minutes = [float(run_rows[t]["agent_minutes"]) for t in tasks if run_rows[t]["agent_minutes"]]
    return {
        "tasks": len(tasks),
        "passed": sum(int(run_rows[t]["passed"]) for t in tasks),
        "fresh_input_tokens": sum(int(run_rows[t]["fresh_input_tokens"]) for t in tasks),
        "cached_input_tokens": sum(int(run_rows[t]["cached_input_tokens"]) for t in tasks),
        "input_tokens": sum(
            int(run_rows[t]["fresh_input_tokens"]) + int(run_rows[t]["cached_input_tokens"]) for t in tasks
        ),
        "output_tokens": sum(int(run_rows[t]["output_tokens"]) for t in tasks),
        "model_calls": sum(int(run_rows[t]["model_calls"]) for t in tasks),
        "cost_usd": round(sum(float(run_rows[t]["cost_usd"]) for t in tasks), 2),
        "median_minutes": round(statistics.median(minutes), 1) if minutes else None,
    }


def main():
    rows = {}
    for row in csv.DictReader(open("data/results.csv")):
        if row["passable"] != "1":
            continue
        rows.setdefault(row["run"], {})[row["task"]] = row
    by_key = {agent["key"]: agent for agent in AGENTS}

    # Four agents, on the tasks every run graded.
    common = sorted(set.intersection(*[set(rows[run]) for agent in AGENTS for run in agent["runs"]]))
    agents = []
    for agent in AGENTS:
        runs = [totals(rows[run], common) for run in agent["runs"]]
        n = len(runs)
        mean = {
            key: sum(run[key] for run in runs) / n
            for key in ("passed", "input_tokens", "fresh_input_tokens", "cached_input_tokens", "output_tokens", "model_calls", "cost_usd")
        }
        agents.append(
            {
                "key": agent["key"],
                "name": agent["name"],
                "when": agent["when"],
                "runs": runs,
                "per_run": {key: round(value, 2) for key, value in mean.items()},
                "per_task": {
                    "input_tokens": round(mean["input_tokens"] / len(common)),
                    "output_tokens": round(mean["output_tokens"] / len(common)),
                    "model_calls": round(mean["model_calls"] / len(common), 1),
                    "cost_usd": round(mean["cost_usd"] / len(common), 4),
                },
                "cost_per_solved_usd": round(mean["cost_usd"] / mean["passed"], 4),
                "cached_share": round(mean["cached_input_tokens"] / mean["input_tokens"], 3),
            }
        )

    # Agency and Pi, attempt by attempt, started together.
    attempts = []
    count = len(by_key["agency"]["runs"])
    for index in range(count):
        a = rows[by_key["agency"]["runs"][index]]
        p = rows[by_key["pi"]["runs"][index]]
        shared = sorted(set(a) & set(p))
        # The attempt number is the digit in the run name: k1 is attempt 1.
        entry = {"attempt": int(by_key["agency"]["runs"][index][1]), "tasks": len(shared), "agency": totals(a, shared), "pi": totals(p, shared)}
        entry["only_agency"] = sum(a[t]["passed"] == "1" and p[t]["passed"] == "0" for t in shared)
        entry["only_pi"] = sum(p[t]["passed"] == "1" and a[t]["passed"] == "0" for t in shared)
        entry["p_value"] = round(sign_test(entry["only_agency"], entry["only_pi"]), 3)
        attempts.append(entry)

    every = sorted(set.intersection(*[set(rows[run]) for key in PAIR for run in by_key[key]["runs"]]))
    passes = {
        key: {t: sum(int(rows[run][t]["passed"]) for run in by_key[key]["runs"]) for t in every}
        for key in PAIR
    }
    pair = {"tasks": len(every), "attempts": count}
    for key in PAIR:
        counts = passes[key]
        pair[key] = {
            "passes": sum(counts.values()),
            "possible": count * len(every),
            "always": sum(c == count for c in counts.values()),
            "sometimes": sum(0 < c < count for c in counts.values()),
            "never": sum(c == 0 for c in counts.values()),
        }
    more_agency = sum(passes["agency"][t] > passes["pi"][t] for t in every)
    more_pi = sum(passes["pi"][t] > passes["agency"][t] for t in every)
    pair["more_often"] = {
        "agency": more_agency,
        "pi": more_pi,
        "same": len(every) - more_agency - more_pi,
        "p_value": round(sign_test(more_agency, more_pi), 3),
    }

    summary = {"common_tasks": len(common), "agents": agents, "attempts": attempts, "pair": pair}
    with open("summary.js", "w") as f:
        f.write("// Written by scripts/build_summary.py from data/results.csv. Do not edit.\n")
        f.write("window.SUMMARY = ")
        json.dump(summary, f, indent=1)
        f.write(";\n")
    print("common tasks", len(common))
    for agent in agents:
        print(agent["name"], agent["per_run"], agent["per_task"], agent["cost_per_solved_usd"], agent["cached_share"])
    print(pair)


main()
