# src/data_processing.py
from src.commonconst import *
from src.prompt import *

def generate_funding_gap_csvs(base_data_path=DATA_BASE_PATH, output_base=FUNDING_GAP_OUTPUT_BASE):
    """Processes all theme Excel files by region and saves funding gap CSVs with Grand Total row."""
    for region in os.listdir(base_data_path):
        region_path = os.path.join(base_data_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".xlsx"):
                continue

            theme_name = file.replace(".xlsx", "")
            file_path = os.path.join(region_path, file)
            try:
                df = pd.read_excel(file_path)

                gap_cols = []
                for year in FUNDING_GAP_YEARS:
                    req = f"{year} Required"
                    avail = f"{year} Available"
                    exp = f"{year} Expenditure"
                    gap = f"{year} Gap"

                    if req in df.columns and avail in df.columns:
                        df[gap] = df[req] - df[avail]
                        gap_cols.extend([req, avail, exp if exp in df.columns else None, gap])

                final_cols = FUNDING_BASE_COLUMNS + [col for col in gap_cols if col is not None]
                df_out = df[final_cols]
                df_out = df_out.groupby("Country", as_index=False).sum(numeric_only=True)

                # Create Grand Total row
                grand_total = df_out.drop(columns=["Country"]).sum(numeric_only=True)
                grand_total["Country"] = "Grand Total"
                df_out = pd.concat([df_out, pd.DataFrame([grand_total])], ignore_index=True)

                # Save output
                region_output_path = os.path.join(output_base, region)
                os.makedirs(region_output_path, exist_ok=True)
                output_file = os.path.join(region_output_path, f"{theme_name}_FundingGaps.csv")
                df_out.to_csv(output_file, index=False)
                print(f"✅ Saved: {output_file}")

            except Exception as e:
                print(f"❌ Failed processing {file_path}: {e}")

def generate_progress_snapshots(base_data_path=DATA_BASE_PATH, output_base=PROGRESS_OUTPUT_BASE):
    """Extracts specified progress tracking columns and saves one CSV per theme per region."""
    for region in os.listdir(base_data_path):
        region_path = os.path.join(base_data_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".xlsx"):
                continue

            theme_name = file.replace(".xlsx", "")
            file_path = os.path.join(region_path, file)
            try:
                df = pd.read_excel(file_path)
                existing_cols = [col for col in PROGRESS_COLUMNS if col in df.columns]

                df_out = df[existing_cols].copy()
                region_output_path = os.path.join(output_base, region)
                os.makedirs(region_output_path, exist_ok=True)

                output_file = os.path.join(region_output_path, f"{theme_name}.csv")
                df_out.to_csv(output_file, index=False)
                print(f"📊 Progress saved: {output_file}")

            except Exception as e:
                print(f"❌ Failed progress extraction for {file_path}: {e}")
def apply_refined_funding_imputation(base_data_path=DATA_BASE_PATH, seed=42):
    """
    Applies refined imputation to all Excel files to simulate variation:
    Required ≥ Available ≥ Expenditure using realistic random decomposition.
    """
    
    np.random.seed(seed)

    for region in os.listdir(base_data_path):
        region_path = os.path.join(base_data_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".xlsx"):
                continue

            file_path = os.path.join(region_path, file)
            try:
                df = pd.read_excel(file_path)

                for year in range(2016, 2029):
                    req_col = f"{year} Required"
                    avail_col = f"{year} Available"
                    exp_col = f"{year} Expenditure"

                    if req_col in df.columns:
                        for i in range(len(df)):
                            required = df.at[i, req_col]
                            if pd.isna(required) or required == 0:
                                continue

                            available_ratio = np.random.uniform(0.6, 0.95)
                            expenditure_ratio = np.random.uniform(0.6, 0.95)

                            df.at[i, avail_col] = round(required * available_ratio, 2)
                            df.at[i, exp_col] = round(df.at[i, avail_col] * expenditure_ratio, 2)

                df.to_excel(file_path, index=False)

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")