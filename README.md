# learningds

A personal study repository for data science with Python. It holds short exercises, the notes behind them, and a set of case-study documents about one AI agent that asks for refunds under an authorisation layer.

The exercise in this repository runs from start to finish on its own. It needs no external data file, cloud account or secret. The case-study documents describe a live system, and they contain no secrets either.

## Contents

| Path | What it is |
| --- | --- |
| `01_explore_sales.py` | First exercise: build a sample table, summarise it, group it, and save a chart |
| `requirements.txt` | The Python packages the exercises use |
| `.gitignore` | Keeps the virtual environment, notebook checkpoints and generated `outputs/` out of git |
| `docs/razorpay-agent-end-to-end.md` | Case study: the refund agent, its authorisation layer and the payment provider, end to end |
| `docs/agent/` | How the agent was built, how it behaves in each scenario, and how stuck states are resolved |
| `docs/razorpay-journey/` | The full journey: timeline, commands and outcomes, incidents, keys by name, approvals, open items, and meeting notes |

## Learning path

Work through these in order. Each step builds on the one before.

1. **Python and the data tools.** Loading, cleaning and summarising tables with pandas; plotting with matplotlib. Current exercise: `01_explore_sales.py`.
2. **Statistics.** Distributions, averages and spread; sampling; what a p-value does and does not tell you.
3. **Modelling.** A simple regression, how to check it, then a classifier and how to judge one.
4. **Systems.** How a model or an agent is wired into real services, what can go wrong, and how to test it. The documents in `docs/` are the worked example for this step.

## Setup

The exercise was run on Python 3.13. Other versions have not been checked.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the first exercise

```bash
python 01_explore_sales.py
```

It prints the first rows, a summary of the numeric columns, and revenue by region. It also saves a bar chart to `outputs/revenue_by_region.png`.

The data is generated with a fixed random seed, so the numbers are the same on every run. To try a different sample, change the `seed` argument of `make_sample_sales`.

## Read the case study

The case study is in three places. Start with the first and go to the others as needed.

- `docs/razorpay-agent-end-to-end.md`: the whole system in one document, from the agent to the payment provider.
- `docs/agent/`: how the agent was built, how it behaves in each scenario, and how each stuck state is resolved. Start at `docs/agent/README.md`.
- `docs/razorpay-journey/`: what happened, in order, with the commands and their results. Start at `docs/razorpay-journey/README.md`.

Each claim in these documents is marked as one of:

- **Code:** read in a repository, with the file named.
- **Configured:** set by hand in the agent builder, so it is not in any repository file.
- **Observed:** seen in a live call or a command's output.
- **Reported:** taken from a report, not checked here.
- **Open:** not built, not tested, or not decided.

At the time of writing, the agent is built but not verified. The approved refund has not yet been run through the agent. Read the documents for how the pieces fit together and for what went wrong along the way, not as a description of a working production system.

## Conventions

- **No secrets in this repository.** No keys, tokens, passwords or connection strings, in code, notebooks, docs or commit messages. Keep them in a password manager. The documents name keys by their file or variable only.
- **Generated files stay out.** Charts, tables and model files go in `outputs/`, which git ignores.
- **Notebooks.** Keep outputs cleared before committing a notebook, so diffs stay readable.
- **Commits.** Short, present-tense subject lines, and a body when the reason isn't obvious from the change.

## Adding an exercise

1. Put the script or notebook at the top level, numbered in the order it should be read, for example `02_...`.
2. Make it run from a clean checkout after `pip install -r requirements.txt`, with no external files.
3. Add a row to the table in "Contents", and a sentence to "Learning path" if it starts a new step.
4. Write any longer explanation in `docs/`.
