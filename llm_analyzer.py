# llm_analyzer.py
from src.commonconst import *

# Initialize Azure client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

def extract_sub_outputs_from_progress(file_path):
    """Extract valid sub-output entries from the saved progress CSV."""
    try:
        df = pd.read_csv(file_path)
        if "Sub-Output" in df.columns:
            sub_outputs = df["Sub-Output"].dropna().astype(str)
            return sub_outputs[sub_outputs.str.len() > 10].tolist()
    except Exception as e:
        print(f"⚠️ Failed to read or extract from {file_path}: {e}")
    return []

def build_analyzer_prompt(theme, sub_outputs):
    bullets = "\n".join(f"- {item}" for item in sub_outputs[:50])
    return Analyzer_PROMPT_TEMPLATE.format(theme=theme, bullets=bullets)

def analyze_suboutput_progress():
    """Run analyzer over all regional progress CSVs and store to 4o_outputs."""
    for region in os.listdir(PROGRESS_OUTPUT_BASE):
        region_path = os.path.join(PROGRESS_OUTPUT_BASE, region)
        if not os.path.isdir(region_path):
            continue

        for file in os.listdir(region_path):
            if not file.endswith(".csv"):
                continue

            theme = file.replace(".csv", "")
            file_path = os.path.join(region_path, file)
            sub_outputs = extract_sub_outputs_from_progress(file_path)

            if not sub_outputs:
                print(f"⚠️ Skipping {file} – no valid sub-output entries found.")
                continue

            # Prepare prompt
            mcp = ModelContext(
                user_role="UN Policy Analyst",
                theme=theme,
                document_path=file_path
            )
            full_prompt = mcp.to_prompt_context() + "\n\n" + build_analyzer_prompt(theme, sub_outputs)

            # Run model
            try:
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                result = response.choices[0].message.content
                if result:
                    output_dir = f"src/outputs/4o_outputs/{region}"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f"{theme}_Output.txt")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(result)
                    print(f"✅ Saved output: {output_path}")
                else:
                    print(f"⚠️ Empty response for {theme} in {region}")

            except Exception as e:
                print(f"❌ API call failed for {theme} in {region}: {e}")

if __name__ == "__main__":
    analyze_suboutput_progress()