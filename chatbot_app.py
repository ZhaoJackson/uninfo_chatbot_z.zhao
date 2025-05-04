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

        df = xl.parse(pivot_sheet, header=2)  # Use third row as header (0-indexed)
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
st.title("🌍 UN INFO 2024 – Thematic Assistant")

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

    # Theme selector
    selected_theme = st.selectbox("Choose a theme", list(THEME_CONFIGS.keys()), key="chat_theme")

    # Clear chat history when theme changes
    if selected_theme != st.session_state.previous_theme:
        st.session_state.chat_history = []
        st.session_state.chat_input = ""
        st.session_state.previous_theme = selected_theme

    # Define chat handler
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
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"Error: {e}"))
        st.session_state.chat_input = ""

    # Chat history display
    with st.container():
        for role, msg in st.session_state.chat_history:
            icon = "🔹" if role == "user" else "🤖"
            st.markdown(f"**{icon} {role.capitalize()}:** {msg}")

    # Input field with Enter key trigger
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
    This tool was built to explore and explain funding data from UN INFO 2024 across African regions.

    - Ask questions using an LLM-based chatbot
    - View data-driven visuals of required funding by country
    - Based on real UN sub-output and pivot table data

    **Created by:** Zichen Zhao (ziche.zhao@un.org)
    **Powered by:** Streamlit + Azure OpenAI + Plotly
    """)