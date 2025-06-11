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

def apply_funding_imputation(base_data_path=DATA_BASE_PATH, seed=42):
    """
    Applies refined funding imputation with cluster-based variation:
    Required ≥ Available ≥ Expenditure within Country + Strategic Priority groups.
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

                if 'Country' not in df.columns or 'Strategic priority' not in df.columns:
                    print(f"⚠️ Missing clustering features in {file_path}, skipping.")
                    continue

                for year in range(2016, 2029):
                    req_col = f"{year} Required"
                    avail_col = f"{year} Available"
                    exp_col = f"{year} Expenditure"

                    if req_col not in df.columns:
                        continue
                    
                    # Cluster-based imputation with category grouping
                    grouped = df.groupby(['Country', 'Strategic priority'])
                    for (country, priority), group in grouped:

                        # Randomized Ratio Generation with Reproducible Seeding
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

                            # Proportional decomposition of Required into Available and Expenditure
                            available = required * avail_ratio
                            expenditure = available * exp_ratio

                            df.at[idx, avail_col] = round(available, 2)
                            df.at[idx, exp_col] = round(expenditure, 2)

                df.to_excel(file_path, index=False)

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")