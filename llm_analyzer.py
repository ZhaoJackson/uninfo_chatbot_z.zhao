# llm_analyzer.py
from src.commonconst import *
from src.prompt import *

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

            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                print(f"❌ Failed to read {file_path}: {e}")
                continue

            # Prepare prompt
            mcp = ModelContext(
                user_role="UN Policy Analyst",
                theme=theme,
                document_path=file_path
            )
            context = mcp.to_prompt_context()
            full_prompt = context + "\n\n" + generate_analyzer_prompt(theme, df)

            try:
                response = client_4o.chat.completions.create(
                    model=DEPLOYMENT_4O,
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