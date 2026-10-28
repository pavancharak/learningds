# learningds

A personal study repository for data science with Python. It holds short exercises and the notes behind them.

Each exercise runs from start to finish on its own. It needs no external data file, cloud account or secret.

## Contents

| Path | What it is |
| --- | --- |
| `01_explore_sales.py` | First exercise: build a sample table, summarise it, group it, and save a chart |
| `requirements.txt` | The Python packages the exercises use |
| `.gitignore` | Keeps the virtual environment, notebook checkpoints and generated `outputs/` out of git |

## Learning path

Work through these in order. Each step builds on the one before.

1. **Python and the data tools.** Loading, cleaning and summarising tables with pandas; plotting with matplotlib. Current exercise: `01_explore_sales.py`.
2. **Statistics.** Distributions, averages and spread; sampling; what a p-value does and does not tell you.
3. **Modelling.** A simple regression, how to check it, then a classifier and how to judge one.
4. **Systems.** How a model or an agent is wired into real services, what can go wrong, and how to test it.

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

## Conventions

- **No secrets in this repository.** No keys, tokens, passwords or connection strings, in code, notebooks, docs or commit messages. Keep them in a password manager.
- **Generated files stay out.** Charts, tables and model files go in `outputs/`, which git ignores.
- **Notebooks.** Keep outputs cleared before committing a notebook, so diffs stay readable.
- **Commits.** Short, present-tense subject lines, and a body when the reason isn't obvious from the change.

## Adding an exercise

1. Put the script or notebook at the top level, numbered in the order it should be read, for example `02_...`.
2. Make it run from a clean checkout after `pip install -r requirements.txt`, with no external files.
3. Add a row to the table in "Contents", and a sentence to "Learning path" if it starts a new step.
4. Write any longer explanation in `docs/`.
