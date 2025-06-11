# src/data_processing.py
from src.commonconst import *

def generate_funding_gap_csvs(base_data_path=IMPUTED_OUTPUT_BASE, output_base=FUNDING_GAP_OUTPUT_BASE):
    """Processes all theme CSVs by region and saves funding gap CSVs with Grand Total row."""
    for region in os.listdir(base_data_path):
        region_path = os.path.join(base_data_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".csv"):
                continue

            theme_name = file.replace("_Imputed.csv", "")
            file_path = os.path.join(region_path, file)
            try:
                df = pd.read_csv(file_path)

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

                grand_total = df_out.drop(columns=["Country"]).sum(numeric_only=True)
                grand_total["Country"] = "Grand Total"
                df_out = pd.concat([df_out, pd.DataFrame([grand_total])], ignore_index=True)

                region_output_path = os.path.join(output_base, region)
                os.makedirs(region_output_path, exist_ok=True)
                output_file = os.path.join(region_output_path, f"{theme_name}_FundingGaps.csv")
                df_out.to_csv(output_file, index=False)
                print(f"✅ Saved: {output_file}")

            except Exception as e:
                print(f"❌ Failed processing {file_path}: {e}")

def generate_progress_snapshots(base_data_path=IMPUTED_OUTPUT_BASE, output_base=PROGRESS_OUTPUT_BASE):
    """Extracts specified progress tracking columns and saves one CSV per theme per region."""
    for region in os.listdir(base_data_path):
        region_path = os.path.join(base_data_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".csv"):
                continue

            theme_name = file.replace("_Imputed.csv", "")
            file_path = os.path.join(region_path, file)
            try:
                df = pd.read_csv(file_path)
                existing_cols = [col for col in PROGRESS_COLUMNS if col in df.columns]

                df_out = df[existing_cols].copy()
                region_output_path = os.path.join(output_base, region)
                os.makedirs(region_output_path, exist_ok=True)

                output_file = os.path.join(region_output_path, f"{theme_name}.csv")
                df_out.to_csv(output_file, index=False)
                print(f"📊 Progress saved: {output_file}")

            except Exception as e:
                print(f"❌ Failed progress extraction for {file_path}: {e}")

def apply_funding_imputation(base_data_path=DATA_BASE_PATH, output_base_path=IMPUTED_OUTPUT_BASE, seed=42):
    """
    Two-stage imputation:
    - Stage 1: Impute 'Required' based on cluster mean using key features, with randomness added for diversity.
    - Stage 2: Impute 'Available' and 'Expenditure' with bounded randomness.
    Applies only for years 2015–2025.
    Outputs CSVs to: src/outputs/data_outputs/imput/{Region}/{Theme}_Imputed.csv
    """
    np.random.seed(seed)

    for region in os.listdir(base_data_path):
        region_path = Path(base_data_path) / region
        if not region_path.is_dir():
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".xlsx"):
                continue

            input_file_path = region_path / file
            try:
                df = pd.read_excel(input_file_path)

                if 'Country' not in df.columns or 'Strategic priority' not in df.columns:
                    print(f"⚠️ Missing clustering features in {input_file_path}, skipping.")
                    continue

                # STAGE 1: Clustered Required Imputation (2015–2025)
                cluster_keys = ["Country", "Strategic priority", "SDG Goals", "QCPR function"]
                for year in range(2015, 2026):
                    req_col = f"{year} Required"
                    if req_col not in df.columns:
                        continue

                    for _, group_df in df.groupby(cluster_keys):
                        idxs = group_df.index
                        base_mean = group_df[req_col].mean()

                        for idx in idxs:
                            if pd.isna(df.at[idx, req_col]) or df.at[idx, req_col] == 0:
                                if not pd.isna(base_mean):
                                    variation = np.random.uniform(0.8, 1.2)
                                    df.at[idx, req_col] = round(base_mean * variation, 2)

                    # Final fallback using row-level mean across Required years
                    if df[req_col].isna().any():
                        row_mean_required = df[[f"{y} Required" for y in range(2015, 2026)
                                                if f"{y} Required" in df.columns]].mean(axis=1)
                        df[req_col] = df[req_col].fillna(row_mean_required)

                # STAGE 2: Impute Available & Expenditure
                for year in range(2015, 2026):
                    req_col = f"{year} Required"
                    avail_col = f"{year} Available"
                    exp_col = f"{year} Expenditure"

                    if req_col not in df.columns:
                        continue

                    grouped = df.groupby(["Country", "Strategic priority"])
                    for (country, priority), group in grouped:
                        base_avail_ratio = np.random.uniform(0.7, 0.9)
                        base_exp_ratio = np.random.uniform(0.7, 0.9)

                        for idx in group.index:
                            required = df.at[idx, req_col]
                            if pd.isna(required) or required == 0:
                                continue

                            noise_avail = np.random.normal(0, 0.05)
                            noise_exp = np.random.normal(0, 0.05)

                            avail_ratio = max(0.4, min(0.95, base_avail_ratio + noise_avail))
                            exp_ratio = max(0.4, min(0.95, base_exp_ratio + noise_exp))

                            df.at[idx, avail_col] = round(required * avail_ratio, 2)
                            df.at[idx, exp_col] = round(required * avail_ratio * exp_ratio, 2)

                region_output_path = Path(output_base_path) / region
                os.makedirs(region_output_path, exist_ok=True)

                output_csv_path = region_output_path / file.replace(".xlsx", "_Imputed.csv")
                df.to_csv(output_csv_path, index=False)

                print(f"💾 Imputed CSV saved: {output_csv_path}")

            except Exception as e:
                print(f"❌ Error processing {input_file_path}: {e}")

def merge_all_progress_data(progress_base_path=PROGRESS_OUTPUT_BASE, output_path=OUTPUT_PATH):
    """Merges all regional and thematic progress CSVs into one master dataset with Region and Theme tags."""
    merged_dfs = []

    for region in os.listdir(progress_base_path):
        region_path = os.path.join(progress_base_path, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".csv"):
                continue

            theme = file.replace(".csv", "")
            file_path = os.path.join(region_path, file)

            try:
                df = pd.read_csv(file_path)
                df.insert(1, "Region", region)
                df.insert(2, "Theme", theme)
                merged_dfs.append(df)

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    if merged_dfs:
        master_df = pd.concat(merged_dfs, ignore_index=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        master_df.to_csv(output_path, index=False)
        print(f"✅ Merged progress data saved to: {output_path}")
    else:
        print("⚠️ No progress data found to merge.")