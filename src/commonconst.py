# src/commonconst.py
from openai import AzureOpenAI
import streamlit as st
import pandas as pd
import re
import os
import streamlit as st
import plotly.express as px

# Azure OpenAI Credentials
AZURE_OPENAI_API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_VERSION = st.secrets["AZURE_OPENAI_API_VERSION"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

# Analyzer Output directory
GPT_OUTPUT_DIR_Africa = "src/outputs/4o_outputs/Africa_Outputs"

# Theme file configuration
THEME_CONFIGS = {
    "Youth": {
        "file": "src/data/Africa/Youth - jeunesse.xlsx",
        "sheets": ["Youth - Pivot Table", "Youth - SubOutputs"]
    },
    "Digital": {
        "file": "src/data/Africa/Digital - numérique.xlsx",
        "sheets": ["Digital - Pivot Table", "Digital - SubOutputs"]
    },
    "Education": {
        "file": "src/data/Africa/Education - éducation.xlsx",
        "sheets": ["Education - Pivot Table", "Education - SubOutputs"]
    },
    "Mining": {
        "file": "src/data/Africa/Mining - Mine.xlsx",
        "sheets": ["Mining - Pivot Table", "Mining - SubOutputs"]
    },
    "IFF - Transnational_Crimes": {
        "file": "src/data/Africa/IFF - Transnational _Crimes.xlsx",
        "sheets": ["IFF & Crime - Pivot Table", "IFF & Crime - SubOutputs"]
    },
}

O1_PROMPT_TEMPLATE = """
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