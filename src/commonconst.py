# commonconst.py
from openai import AzureOpenAI
import numpy as np
import streamlit as st
import pandas as pd
import re
import os
import plotly.express as px
from io import StringIO
from xgboost import XGBRegressor

# Azure OpenAI Credentials
# 4o for Tab 1 + llm_analyzer
client_4o = AzureOpenAI(
    api_key=st.secrets["AZURE_OPENAI_4O_API_KEY"],
    api_version=st.secrets["AZURE_OPENAI_4O_API_VERSION"],
    azure_endpoint=st.secrets["AZURE_OPENAI_4O_ENDPOINT"]
)
DEPLOYMENT_4O = st.secrets["AZURE_OPENAI_4O_DEPLOYMENT"]

# o1 for Tab 2 + Tab 3
client_o1 = AzureOpenAI(
    api_key=st.secrets["AZURE_OPENAI_O1_API_KEY"],
    api_version=st.secrets["AZURE_OPENAI_O1_API_VERSION"],
    azure_endpoint=st.secrets["AZURE_OPENAI_O1_ENDPOINT"]
)
DEPLOYMENT_O1 = st.secrets["AZURE_OPENAI_O1_DEPLOYMENT"]

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

# === Modeling for Funding Analysis ===

# Root directory containing all regional funding CSVs
FUNDING_DATA_DIR = "src/outputs/progress"

# Years to use for historical training
TRAIN_YEARS = list(range(2016, 2025))
FORECAST_YEAR = 2026
FUNDING_VARS = ["Required", "Available", "Expenditure"]


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
