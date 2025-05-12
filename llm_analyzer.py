# llm_analyzer.py

from src.commonconst import *
from src.data_processing import *

# Initialize Azure client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# Ensure output directory exists
os.makedirs(GPT_OUTPUT_DIR_Africa, exist_ok=True)

def analyze_theme(theme, config):
    print(f"\n🔍 Processing theme: {theme}")

    # Step 1: Extract sub-output text from Excel
    try:
        sub_outputs = extract_sub_outputs(config['file'], config['sheets'])
    except Exception as e:
        print(f"❌ Error reading data for {theme}: {e}")
        return

    if not sub_outputs:
        print(f"⚠️ Skipping {theme} – no valid sub-output entries found.")
        return

    # Step 2: Build model context (MCP) for this theme
    mcp = ModelContext(
        user_role="UN Policy Analyst",  # You can make this dynamic later if needed
        theme=theme,
        document_path=config['file']
    )

    # Step 3: Build prompt by combining MCP and theme-specific sub-outputs
    context_prompt = mcp.to_prompt_context()
    theme_prompt = build_prompt(theme, sub_outputs)
    full_prompt = context_prompt + "\n\n" + theme_prompt

    # Step 4: Call LLM using Azure OpenAI
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
            # Save response to file
            output_path = os.path.join(GPT_OUTPUT_DIR_Africa, f"{theme}_Output.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)

            print(f"✅ Output saved: {output_path}")
        else:
            print(f"⚠️ o1 model returned empty content for {theme}")

    except Exception as e:
        print(f"❌ Error during Azure o1 call for {theme}: {e}")

if __name__ == "__main__":
    for theme, config in THEME_CONFIGS.items():
        analyze_theme(theme, config)