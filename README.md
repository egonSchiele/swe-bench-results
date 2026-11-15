# What four coding agents cost on SWE-bench Verified

Four coding agents on all 500 tasks of SWE-bench Verified, with the same model and the same sandboxes. They solve about the same share of tasks. What separates them is how many tokens they spend.

- **Agency**: the minimal brain of the [Agency](https://github.com/egonSchiele/agency-lang) agent.
- **Pi** 1.5.2, **OpenCode** 1.19.5, and **mini-SWE-agent** 2.4.6.

Open `index.html` for the results with charts.

## Result

Per run, on the 470 tasks graded in every run:

| | Input tokens | Output tokens | Model calls per task | Estimated cost | Cost per solved task | Solved |
|---|---|---|---|---|---|---|
| Agency, mean of 5 runs | 256M | 5.9M | 27.8 | $12.01 | 3.3¢ | 76.6% |
| Pi 1.5.2, mean of 5 runs | 285M | 6.5M | 29.2 | $13.27 | 3.7¢ | 77.2% |
| OpenCode 1.19.5, one run | 376M | 5.7M | 31.3 | $15.67 | 4.4¢ | 76.0% |
| mini-SWE-agent 2.4.6, one run | 615M | 7.1M | 46.2 | $24.13 | 6.7¢ | 76.6% |

Against Agency, Pi used 11% more input tokens, OpenCode 47% more, and mini-SWE-agent 140% more. Agency used fewer input and output tokens than Pi in every one of the five attempts.

Every run solved between 75.1% and 78.9% of the tasks. Agency and Pi were run five times side by side, and on tasks solved they are level.

## Setup

- **Benchmark:** SWE-bench Verified, 500 tasks, one attempt per task per run.
- **Model:** GLM 5.3 Flash through OpenRouter, pinned to the Z.AI host, reasoning effort high for every agent.
- **Agency:** `agency agent --brain minimal`, commit `e0d23da8f` for attempts 1 and 2, `a80b90157` for attempt 3, `95b344b63` for attempt 4, and for attempt 5 `f13bfe1db` with one unmerged change: the file tools take a single path argument. A separate 99-task run found the first two commits level (83 and 82 solved). Five runs, each started together with a Pi run. Attempts 1 and 2 ran at the same time on the same build.
- **Pi:** `@earendil-works/pi-coding-agent` 1.5.2, thinking high. Five runs.
- **OpenCode:** 1.19.5. One run, on 11 November 2026.
- **mini-SWE-agent:** 2.4.6. One run, on 13 November 2026.
- **Network:** each sandbox could reach the model and nothing else while the agent ran, so an agent could not look up the upstream fix or install a newer package.
- **Sandboxes and grading:** Harbor 0.17.1 on Daytona, graded by Harbor's SWE-bench adapter with each task's own tests.
- **Dates:** Agency and Pi attempts 1 and 2 on 13 November 2026, attempts 3 and 4 on 14 November 2026, attempt 5 overnight from 14 to 15 November 2026.

## What is left out

- **Eight tasks that cannot pass here.** With the task's own reference fix applied, they still fail in these sandboxes: `astropy__astropy-7606`, `django__django-10097`, `psf__requests-1724`, `psf__requests-1766`, `psf__requests-1921`, `psf__requests-2317`, `psf__requests-5414`, `scikit-learn__scikit-learn-14710`. They are in the CSV with `passable = 0`.
- **Trials that failed on the sandbox side.** A trial that ended in a sandbox error has no row. Attempt 3 had the most, which is why it compares 478 tasks where the other four compare 487 to 491.
- A comparison between the agents always uses only the tasks both were graded on.

## Files

| Path | What it holds |
|---|---|
| `data/results.csv` | One row per run and task: `run`, `agent`, `task`, `repo`, `passable`, `passed`, `fresh_input_tokens`, `cached_input_tokens`, `output_tokens`, `model_calls`, `cost_usd`, `agent_minutes`, `patch_lines`, `error` |
| `scripts/build_summary.py` | Computes every figure on the page from the CSV and writes `summary.js` |
| `index.html`, `summary.js` | The results page |

Runs are named `k1-agency-minimal`, `k1-pi`, and so on, where `k1` to `k5` are attempts 1 to 5. `ref-opencode` and `ref-mini` are the single runs of the other two agents. For OpenCode, reasoning tokens are added to output tokens, as the other agents already count them.

`cost_usd` is an estimate from token counts at $0.15 per million fresh input tokens, $0.03 per million cached, and $0.50 per million output. `error` is `AgentTimeoutError` for a run stopped at the time limit, or `NonZeroAgentExitCodeError` for an agent that exited with an error; such a run is graded on what it left. `patch_lines` is the length of the diff the agent left.

The agents' patches, the grader's reports, and the raw transcripts are not published.

## What to keep in mind

- **Run-to-run variation is large.** One agent's score moved by about three points between its lowest and highest attempt. A smaller difference between two agents means little.
- **One model, one benchmark.** These results say nothing about another model, and SWE-bench Verified is Python bug fixing in twelve projects, with more than 40% of the tasks from Django.

## Rebuilding the page

```
python3 scripts/build_summary.py
```
