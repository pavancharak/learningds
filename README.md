# learningds

Notes, scripts and exercises for learning data science with Python.

## Learning path

1. **Python and data tools.** Loading, cleaning and summarising tables with pandas, and plotting with matplotlib. Start with `01_explore_sales.py`.
2. **Statistics.** Distributions, averages and spread, and what a p-value does and doesn't say.
3. **Modelling.** Fitting and checking a simple regression, then a classifier.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python 01_explore_sales.py
```

The script prints a summary and saves a chart to `outputs/`. The `outputs/` folder is ignored by git, so generated files stay out of the repository.

## Layout

- `01_explore_sales.py`: first exercise, using a small sample dataset built in the script.
- `requirements.txt`: the packages the exercises need.
- `outputs/`: generated charts and tables, not committed.
