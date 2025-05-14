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

def generate_progress_prompt(theme, country, df):
    display_df = df.copy()
    display_str = display_df.head(50).to_csv(index=False)

    return f"""
You are a UN development policy analyst reviewing progress in **{country}** for the theme **{theme}**.

Analyze the following structured table and answer:
1. What are the major areas of support the UN is working on in this country under this theme?
2. How well is the financial implementation (Required vs. Available vs. Expenditure from 2016–2028) aligned with these efforts?
3. Does the data suggest that support is **on track**, **underfunded**, or **inefficient**?

Respond using evidence from the table below and give a reasoned assessment.

Data snapshot:
Provide your output in:
- Main Support Areas
- Financial Performance
- Overall Assessment
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