from src.data_processing import *
from src.commonconst import *

def main():
    print("💸 Running cluster-aware funding imputation...")
    apply_funding_imputation()
    print("✅ Cluster-aware variation applied.")

    print("🔄 Starting funding gap data processing using imputed data...")
    generate_funding_gap_csvs()
    print("✅ Funding gap CSVs generated.")

    print("📊 Starting progress snapshot extraction using imputed data...")
    generate_progress_snapshots()
    print("✅ Progress snapshot CSVs generated.")

    print("🧩 Merging all progress data...")
    merge_all_progress_data()
    print("✅ Merged dataset created.")

if __name__ == "__main__":
    main()