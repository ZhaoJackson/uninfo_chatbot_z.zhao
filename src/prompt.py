# src/prompt.py

# === Tab 1: Chatbot Prompt (Interactive Q&A) ===
def generate_chatbot_prompt(context, model_output, df, user_query):
    display_df = df.copy()
    if "Country" in display_df.columns:
        display_df = display_df[display_df["Country"] != "Grand Total"]
    display_str = display_df.head(50).to_csv(index=False)

    return f"""{context}

Context from model analysis:
{model_output}

Context from structured programmatic data (sample rows shown):
Now answer the following question clearly and concisely:
Q: {user_query}
A:"""

# === Tab 2: Visual Insights Prompt (Funding Gaps) ===
def generate_visual_prompt(theme, country=None):
    return f"""
You are an expert UN data analyst using the OpenAI o1 model.

Generate a time-series insight from the funding data related to the theme: "{theme}"{f" in {country}" if country else ""}.

Please interpret:
- Required vs. Available vs. Expenditure trends (2016–2024)
- Identify gaps or volatility over years
- Summarize insights in 3–4 policy-relevant sentences
"""

# === Tab 3: Thematic Progress Table Prompt (Filtered Summary) ===
def generate_progress_prompt(theme, selected_country, rows):
    bullet_points = "\n".join(f"- {row}" for row in rows)
    return f"""
You are summarizing the progress of the UN's work on the theme **{theme}** in **{selected_country}**.

Based on the extracted sub-outputs below, answer:
1. What are 3–4 key areas of focus in the country for this theme?
2. Any gaps or areas needing improvement?

Sub-Output Entries:
{bullet_points}

Provide a structured summary and note any regional trends if visible.
"""

# === llm_analyzer Prompt (Batch Summarization for Output) ===
def generate_analyzer_prompt(theme, df):
    display_df = df.copy()
    if "Country" in display_df.columns:
        display_df = display_df[display_df["Country"] != "Grand Total"]
    display_str = display_df.head(50).to_csv(index=False)
    return f"""
You are an advanced UN policy analyst AI assistant. Your task is to assess and summarize structured Cooperation Framework (CF JWP) data for the theme: **{theme}**.

Based on the dataset below, perform the following:
1. Identify the **4 main areas of support** that the UN is focusing on under this theme. Use evidence from the Strategic Priority, Output, Outcome, or Sub-Output columns.
2. Highlight any **emerging challenges or gaps in implementation**, particularly in delivery, coordination, or policy alignment.
3. Analyze the **financial performance** across the years (Required, Available, Expenditure columns from 2016–2028). Classify the financial trend as **positive, negative, or neutral**, and summarize your rationale.
4. Reflect on whether the UN’s support is **comprehensive and well-distributed** based on countries and funding coverage.

Data snapshot:
Deliver your output in 3 structured sections: 
- Main Areas of Support
- Key Challenges
- Financial Situation Summary
"""