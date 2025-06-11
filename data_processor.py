from src.data_processing import *
from src.commonconst import *

def main():
    print("💸 Running refined funding imputation...")
    apply_refined_funding_imputation()
    print("✅ Funding variation introduced.")

    print("🔄 Starting funding gap data processing...")
    generate_funding_gap_csvs(base_data_path=DATA_BASE_PATH, output_base=FUNDING_GAP_OUTPUT_BASE)
    print("✅ Funding gap CSVs generated.")

    print("📊 Starting progress snapshot extraction...")
    generate_progress_snapshots(base_data_path=DATA_BASE_PATH, output_base=PROGRESS_OUTPUT_BASE)
    print("✅ Progress snapshot CSVs generated.")

if __name__ == "__main__":
    main()