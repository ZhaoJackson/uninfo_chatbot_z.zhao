from src.commonconst import *

# ========== SHARED FUNCTIONS ==========

@st.cache_data
def load_model_output(theme):
    filepath = os.path.join(O1_OUTPUT_DIR, f"{theme}_Output.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "(No model output found for this theme.)"

@st.cache_data
def summarize_excel_data(theme):
    config = THEME_CONFIGS.get(theme)
    if not config:
        return "Theme not found."
    try:
        data = pd.read_excel(config['file'], sheet_name=config['sheets'])
        df_all = []
        for sheet_name, df in data.items():
            df_all.append(f"\n--- {sheet_name} ---\n")
            sample = df.head(3).to_string(index=False)
            df_all.append(sample)
        return "\n".join(df_all)
    except Exception as e:
        return f"Error reading data: {e}"

@st.cache_data
def generate_funding_chart(theme):
    config = THEME_CONFIGS.get(theme)
    if not config:
        return None, None
    try:
        xl = pd.ExcelFile(config['file'])
        pivot_sheet = next((s for s in xl.sheet_names if "pivot" in s.lower()), None)
        if not pivot_sheet:
            return None, None

        df = xl.parse(pivot_sheet, header=2)
        df = df.dropna(subset=[df.columns[0]])
        df = df.dropna(axis=1, how='all')

        if 'Row Labels' in df.columns:
            df.rename(columns={"Row Labels": "Country"}, inplace=True)
        else:
            df.columns.values[0] = "Country"

        req_col = next((c for c in df.columns if "required" in str(c).lower()), None)
        avail_col = next((c for c in df.columns if "available" in str(c).lower()), None)
        fund_col = next((c for c in df.columns if "funding" in str(c).lower()), None)

        df[req_col] = pd.to_numeric(df[req_col], errors='coerce')
        if avail_col:
            df[avail_col] = pd.to_numeric(df[avail_col], errors='coerce')
        if fund_col:
            df[fund_col] = pd.to_numeric(df[fund_col], errors='coerce')

        df = df.dropna(subset=[req_col])

        bar_fig = px.bar(
            df.sort_values(by=req_col, ascending=False).head(10),
            x="Country", y=req_col,
            title=f"Top 10 Countries by Required Funding ({theme})",
            labels={"Country": "Country", req_col: "Required Funding (USD)"}
        )

        values = [df[req_col].sum()]
        labels = ["2024 Required"]
        if avail_col:
            values.append(df[avail_col].sum())
            labels.append("2024 Available")
        if fund_col:
            values.append(df[fund_col].sum())
            labels.append("2024 Funding")

        pie_fig = px.pie(
            names=labels,
            values=values,
            title=f"Grand Total Breakdown ({theme})"
        )

        return bar_fig, pie_fig
    except Exception as e:
        return None, None

def build_combined_prompt(theme, model_summary, data_snippet, user_question):
    return f"""
You are an AI assistant answering questions based on UN INFO 2024 programming data in Africa.

Theme: {theme}

Context from model analysis:
{model_summary}

Context from raw sub-output data:
{data_snippet}

Now answer the following question clearly and concisely:
Q: {user_question}
A:"""

# Azure client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# ========== STREAMLIT APP ==========

st.set_page_config(page_title="UN INFO Chatbot", layout="wide")
st.title("🇺🇳 United Nations Joint WorkPlans – Thematic Data Assistant")

tabs = st.tabs(["💬 Chatbot", "📊 Visual Insights", "📘 About"])

# --- TAB 1: CHATBOT ---
with tabs[0]:
    st.header("💬 Ask a Question")

    if "previous_theme" not in st.session_state:
        st.session_state.previous_theme = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""
    if "chat_feedback" not in st.session_state:
        st.session_state.chat_feedback = []

    selected_theme = st.selectbox("Choose a theme", list(THEME_CONFIGS.keys()), key="chat_theme")

    # Clear chat if theme changes
    if selected_theme != st.session_state.previous_theme:
        st.session_state.chat_history = []
        st.session_state.chat_input = ""
        st.session_state.chat_feedback = []
        st.session_state.previous_theme = selected_theme

    def handle_input():
        user_query = st.session_state.chat_input.strip()
        if not user_query:
            return
        model_output = load_model_output(selected_theme)
        data_snippet = summarize_excel_data(selected_theme)
        prompt = build_combined_prompt(selected_theme, model_output, data_snippet, user_query)
        try:
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.chat_history.append(("user", user_query))
            st.session_state.chat_history.append(("assistant", answer))
            st.session_state.chat_feedback.append(None)
        except Exception as e:
            error_msg = f"Error: {e}"
            st.session_state.chat_history.append(("assistant", error_msg))
            st.session_state.chat_feedback.append(None)
        st.session_state.chat_input = ""

    # Display chat
    with st.container():
        for i, (role, msg) in enumerate(st.session_state.chat_history):
            icon = "🇺🇳" if role == "user" else "🤖"
            if role == "assistant":
                st.markdown(f"**{icon} Assistant:**")
                st.code(msg, language="text")
                feedback = st.radio(
                    "Was this response helpful?",
                    ["👍 Yes", "👎 No", "No Feedback"],
                    index=2,
                    key=f"feedback_{i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                st.session_state.chat_feedback[i // 2] = feedback if feedback != "No Feedback" else None
            else:
                st.markdown(f"**{icon} User:** {msg}")

    st.text_input("Type your question and press Enter", key="chat_input", on_change=handle_input)

# --- TAB 2: VISUALS ---
with tabs[1]:
    st.header("📊 Funding Overview")
    selected_theme = st.selectbox("Select theme for charts", list(THEME_CONFIGS.keys()), key="vis_theme")
    bar_fig, pie_fig = generate_funding_chart(selected_theme)
    if bar_fig:
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.warning("Bar chart not available for selected theme.")
    if pie_fig:
        st.plotly_chart(pie_fig, use_container_width=True)
    else:
        st.warning("Pie chart not available for selected theme.")

# --- TAB 3: ABOUT ---
with tabs[2]:
    st.header("📘 About This App")
    
    st.markdown("""
### Our Mission
This assistant supports evidence-based decision-making by making UN INFO 2024 programming data in Africa accessible and actionable.  
It enables policy experts, UN staff, and researchers to interact with data-driven insights from Cooporation Framework  Joint Workplans (JWPs), using an AI-powered chatbot and visualizations.

---

### Background
This tool was developed in preparation for the DCO ASG Africa Retreat (May 2025) to:
- Analyze sub-output level programming data from 49+ UN Country Teams (UNCTs)
- Cover six thematic areas: **Youth**, **Education**, **Digital**, **Mining**, **Education in Crisis**, and **IFF & Transnational Crime**
- Leverage UN INFO datasets uploaded and validated by UNCTs as of April 2025

The data comes from publicly available **Cooperation Framework (CF) JWPs** across Africa and includes both English and French content.

---

### How It Works
The assistant runs on **Azure AI Foundry**, using enterprise-secure large language models (OpenAI o1) within UN infrastructure. The process includes:

1. **Pre-processing:** Clean and structure open-ended programming data
2. **Prompt Engineering:** Apply thematic LLM prompts to extract insights
3. **Output Generation:** Summarize themes, challenges, and country examples
4. **Validation:** Reviewed with Microsoft Co-Pilot and cross-checked with experts

All model interactions happen within a **private, role-secured environment**, ensuring compliance with UN cybersecurity and data privacy policies.

---

### What You Can Do
- **Ask questions** via the chatbot on UN programming priorities, funding gaps, or thematic support
- **View funding visualizations** by country and theme
- **Explore outputs** from real programming data aligned with UNCT reporting

---

### Contact Us
**Developer:** Zichen Zhao (Jackson)
**Email:** ziche.zhao@un.org  
**Organization:** UN Development Coordination Office (UNDCO)

---
""")