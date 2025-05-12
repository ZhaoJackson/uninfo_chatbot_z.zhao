# commonconst.py
from openai import AzureOpenAI
import streamlit as st
import pandas as pd
import re
import os
import plotly.express as px

# Azure OpenAI Credentials
AZURE_OPENAI_API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_VERSION = st.secrets["AZURE_OPENAI_API_VERSION"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

# Directory paths
DATA_BASE_PATH = "src/data"
FUNDING_GAP_OUTPUT_BASE = "src/outputs/data_outputs/funding"
PROGRESS_OUTPUT_BASE = "src/outputs/data_outputs/progress"
ANALYZER_OUTPUT_BASE = "src/outputs/4o_outputs"

# Year range for funding gap calculation
FUNDING_GAP_YEARS = list(range(2016, 2025))
PLOT_YEAR_RANGE = (2016, 2024)

# Default columns
FUNDING_BASE_COLUMNS = ["Country"]

# Columns to extract for progress overview
PROGRESS_COLUMNS = [
    "Country", "Plan name", "Strategic priority", "Outcome", "Output", "Sub-Output",
    "SDG Targets", "SDG Goals", "QCPR function",
    "Total required resources", "Total available resources", "Total expenditure resources",
] + [f"{year} {metric}" for year in range(2016, 2029) for metric in ["Required", "Available", "Expenditure"]]

# User roles based on column relevance
USER_ROLES = [
    "Strategic Planner",
    "Results-Based Manager",
    "SDG Analyst",
    "Resident Coordinator",
    "Programme Officer",
    "Policy Specialist"
]

Analyzer_PROMPT_TEMPLATE = """
You are an AI assistant analyzing UN INFO Cooperation Framework (CF JWP) data from 2024.

Theme: {theme}

Based on the following extracted sub-output entries from UN country programming in Africa, please answer:

1. What are the 4 main areas of focus for {theme} in Africa where the UN is supporting (2024)? For each area, identify the main theme (e.g., Economic Empowerment, Education Access, Health Systems) and briefly illustrate the specific focus within that theme using 1–2 sentences.
2. What are potential challenges or gaps in support?

Data:
{bullets}

Please return:
- A list of 4 main areas of focus, each with a theme label and 1–2 sentence illustration
- 2–3 sentences summarizing key challenges/gaps
"""

class ModelContext:
    def __init__(self, user_role, theme, document_path, interaction_history=None):
        self.user_role = user_role
        self.theme = theme
        self.document_path = document_path
        self.interaction_history = interaction_history or []

    def update_history(self, user_input, model_output):
        self.interaction_history.append({"user": user_input, "model": model_output})

    def to_prompt_context(self):
        return f"""You are assisting a {self.user_role} exploring data on the theme of {self.theme}.
        Refer to structured data from: {self.document_path}.
        Keep answers concise, policy-relevant, and privacy-respecting."""
