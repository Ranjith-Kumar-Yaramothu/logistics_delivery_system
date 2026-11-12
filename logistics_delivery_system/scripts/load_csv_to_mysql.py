
from pathlib import Path
import argparse
import sys

import pandas as pd
from sqlalchemy import text

from backend.database import engine
from backend.services.validation import validate_dataset


DATA_DIR = Path("data/generated")

# Delete child tables before parent tables.
DELETE_ORDER = [
    "event_history",
    "delivery_outcomes",
    "route_stops",
    "routes",
    "time_windows",
    "deliveries",
    "shifts",
    "orders",
    "vehicle_capacities",
    "travel_time_matrix",
    "drivers",
    "vehicles",
    "customer_sites"
]

# Insert parent tables before child tables.
LOAD_ORDER = [
    "customer_sites",
    "vehicles",
    "vehicle_capacities",
    "drivers",
    "orders",
    "shifts",
    "deliveries",
    "time_windows",
    "travel_time_matrix"
]

READ_BATCH_SIZE = 5000
INSERT_BATCH_SIZE = 500


def load_csv(connection, table):
    path = DATA_DIR / f"{table}.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing CSV file: {path}"
        )

    total_loaded = 0

    for chunk in pd.read_csv(
        path,
        chunksize=READ_BATCH_SIZE
    ):
        chunk.to_sql(
            name=table,
            con=connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=INSERT_BATCH_SIZE
        )

        total_loaded += len(chunk)

        print(
            f"{table}: loaded {total_loaded} rows"
        )

    return total_loaded


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing project data before loading CSVs"
    )

    args = parser.parse_args()

    if not args.reset:
        print(
            "Loading cancelled. Use --reset only after "
            "backing up your database."
        )
        sys.exit(1)

    # Validate before touching the database.
    print("Validating generated CSV files...")

    validation = validate_dataset()

    if not validation["valid"]:
        print("Dataset validation failed:")

        for error in validation["errors"]:
            print(f"- {error}")

        sys.exit(1)

    print("Dataset validation passed.")

    # Verify every required CSV exists before deleting anything.
    for table in LOAD_ORDER:
        path = DATA_DIR / f"{table}.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Required CSV file missing: {path}"
            )

    print("\nStarting database replacement...")

    try:
        with engine.begin() as connection:

            # Clear old project data.
            print("\nRemoving existing project records...")

            for table in DELETE_ORDER:
                connection.execute(
                    text(f"DELETE FROM `{table}`")
                )

                print(f"Cleared {table}")

            # Import the newly generated datasets.
            print("\nLoading new datasets...")

            for table in LOAD_ORDER:
                count = load_csv(connection, table)

                print(
                    f"Completed {table}: {count} rows"
                )

        print("\nDatabase loading completed successfully.")

    except Exception as exc:
        print("\nDatabase loading failed.")
        print(f"Error: {exc}")
        print("The database transaction was rolled back.")
        raise


if __name__ == "__main__":
    main()
