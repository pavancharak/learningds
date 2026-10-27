"""First exercise: load a table, summarise it, and plot one comparison.

The data is generated here, so the script runs without external files.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).parent / "outputs"


def make_sample_sales(rows: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regions = rng.choice(["North", "South", "East", "West"], size=rows)
    units = rng.poisson(lam=20, size=rows)
    price = rng.normal(loc=12.5, scale=1.5, size=rows).round(2)
    return pd.DataFrame(
        {
            "region": regions,
            "units": units,
            "price": price,
            "revenue": (units * price).round(2),
        }
    )


def main() -> None:
    sales = make_sample_sales()

    print("First rows:")
    print(sales.head(), "\n")

    print("Summary of numeric columns:")
    print(sales.describe().round(2), "\n")

    by_region = (
        sales.groupby("region")
        .agg(orders=("units", "size"), total_revenue=("revenue", "sum"))
        .sort_values("total_revenue", ascending=False)
    )
    print("Revenue by region:")
    print(by_region.round(2), "\n")

    OUTPUT_DIR.mkdir(exist_ok=True)
    ax = by_region["total_revenue"].plot(kind="bar", title="Total revenue by region")
    ax.set_ylabel("Revenue")
    plt.tight_layout()
    chart = OUTPUT_DIR / "revenue_by_region.png"
    plt.savefig(chart)
    print(f"Chart saved to {chart}")


if __name__ == "__main__":
    main()
