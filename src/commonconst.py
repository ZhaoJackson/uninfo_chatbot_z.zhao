# commonconst.py
from openai import AzureOpenAI
import streamlit as st
import pandas as pd
import re
import os
import plotly.express as px
from io import StringIO

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
