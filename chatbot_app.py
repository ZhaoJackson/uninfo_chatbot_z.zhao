# chatbot_app.py
from src.commonconst import *
from src.data_processing import *
from src.prompt import *

# ========== SHARED FUNCTIONS ==========
@st.cache_data
def load_model_output(region, theme):
    filepath = os.path.join(ANALYZER_OUTPUT_BASE, region, f"{theme}_Output.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "(No model output found for this theme.)"

# ========== STREAMLIT APP ==========
st.set_page_config(page_title="UN INFO Chatbot", layout="wide")
st.title("\U0001F1FA\U0001F1F3 United Nations Joint Work Plans – Thematic Data Assistant")

with st.sidebar:
    st.header("🔐 User Context")
    selected_user_role = st.selectbox("Choose your role", USER_ROLES, index=0)

tabs = st.tabs(["💬 Chatbot", "📊 Visual Insights", "📈 Thematic Progress", "📘 About"])

# Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# --- TAB 1: CHATBOT ---
with tabs[0]:
    st.header("\U0001F4AC Ask a Question")

    region_options = sorted([
        d for d in os.listdir(ANALYZER_OUTPUT_BASE)
        if os.path.isdir(os.path.join(ANALYZER_OUTPUT_BASE, d))
    ])
    selected_region = st.selectbox("Select Region", region_options, key="region_chat")
    theme_files = os.listdir(os.path.join(ANALYZER_OUTPUT_BASE, selected_region))
    theme_options = [f.replace("_Output.txt", "") for f in theme_files if f.endswith("_Output.txt")]
    selected_theme = st.selectbox("Choose a Theme", theme_options, key="chat_theme")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""
    def handle_input():
        user_query = st.session_state.chat_input.strip()
        if not user_query:
            return

        model_output = load_model_output(selected_region, selected_theme)
        df_path = os.path.join(PROGRESS_OUTPUT_BASE, selected_region, f"{selected_theme}.csv")
        df = pd.read_csv(df_path)

        # Missing initialization (must be added)
        mcp = ModelContext(
            user_role=selected_user_role,
            theme=selected_theme,
            document_path=f"progress/{selected_region}/{selected_theme}.csv"
        )
        context_prompt = mcp.to_prompt_context()

        full_prompt = generate_chatbot_prompt(context_prompt, model_output, df, user_query)

        try:
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.chat_history.append(("user", user_query))
            st.session_state.chat_history.append(("assistant", answer))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"Error: {e}"))

        st.session_state.chat_input = ""

    for role, msg in st.session_state.chat_history:
        icon = "\U0001F1FA\U0001F1F3" if role == "user" else "\U0001F916"
        st.markdown(f"**{icon} {role.title()}:** {msg}")

    st.text_input("Type your question and press Enter", key="chat_input", on_change=handle_input)

    if not st.session_state.chat_history:
        with st.expander("Where to Get Data?"):
            st.markdown(
                """
                The data is downloaded from [UN INFO](https://uninfo.org/data-explorer/cooperation-framework/activity-report), 
                where you can access the data by selecting **"Search by Name/Code"** in Additional filters 
                and download the CSV file to your local machine.

                We integrate with the **OpenAI o1 & 4o model** to process the uploaded data, 
                mainly to **summarize your queries intelligently**.
                """
            )

    st.caption("© 2025 Zichen Zhao. All rights reserved. Use of this app is permitted via authorized access only. Redistribution or reuse of code is prohibited.")

# --- TAB 2: VISUALS ---
with tabs[1]:
    st.header("\U0001F4CA Funding Overview")

    region_options = sorted([
        d for d in os.listdir(FUNDING_GAP_OUTPUT_BASE)
        if os.path.isdir(os.path.join(FUNDING_GAP_OUTPUT_BASE, d))
    ])
    selected_region = st.selectbox("Select Region", region_options, key="region_vis")
    theme_files = [
        f for f in os.listdir(os.path.join(FUNDING_GAP_OUTPUT_BASE, selected_region))
        if f.endswith(".csv") and os.path.isfile(os.path.join(FUNDING_GAP_OUTPUT_BASE, selected_region, f))
    ]
    themes = sorted([f.replace("_FundingGaps.csv", "") for f in theme_files])

    selected_themes = st.multiselect("Select Themes", themes, default=themes)
    year_range = st.slider("Select Year Range", min_value=PLOT_YEAR_RANGE[0], max_value=PLOT_YEAR_RANGE[1], value=PLOT_YEAR_RANGE)

    plot_data = []
    for theme in selected_themes:
        file_path = os.path.join(FUNDING_GAP_OUTPUT_BASE, selected_region, f"{theme}_FundingGaps.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df = df[df["Country"] != "Grand Total"]
            for year in range(year_range[0], year_range[1] + 1):
                col = f"{year} Gap"
                if col in df.columns:
                    plot_data.append({"Year": year, "Theme": theme, "Gap": df[col].sum()})

    if plot_data:
        df_plot = pd.DataFrame(plot_data)
        fig = px.line(df_plot, x="Year", y="Gap", color="Theme", markers=True,
                      title="Funding Gaps by Theme and Year")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data to display.")
    st.caption("© 2025 Zichen Zhao. All rights reserved. Use of this app is permitted via authorized access only. Redistribution or reuse of code is prohibited.")

# --- TAB 3: PROGRESS TABLE ---
with tabs[2]:
    st.header("\U0001F4C8 Thematic Progress Table")

    region_options = sorted([
        d for d in os.listdir(PROGRESS_OUTPUT_BASE)
        if os.path.isdir(os.path.join(PROGRESS_OUTPUT_BASE, d))
    ])
    selected_region = st.selectbox("Region", region_options, key="region_progress")

    theme_files = [
        f for f in os.listdir(os.path.join(PROGRESS_OUTPUT_BASE, selected_region))
        if f.endswith(".csv") and os.path.isfile(os.path.join(PROGRESS_OUTPUT_BASE, selected_region, f))
    ]
    theme_options = sorted([f.replace(".csv", "") for f in theme_files])
    selected_theme = st.selectbox("Theme", theme_options, key="theme_progress")

    df = pd.read_csv(os.path.join(PROGRESS_OUTPUT_BASE, selected_region, f"{selected_theme}.csv"))
    country_options = sorted(df["Country"].dropna().unique())
    selected_country = st.selectbox("Country", country_options)

    filtered_df = df[df["Country"] == selected_country]
    st.dataframe(filtered_df, use_container_width=True)

    # Bar chart for total required/available/expenditure
    st.subheader("Resource Overview for Selected Country")
    if not filtered_df.empty:
        totals = filtered_df[[
            "Total required resources",
            "Total available resources",
            "Total expenditure resources"
        ]].sum()
        bar_data = pd.DataFrame({
            "Category": totals.index,
            "Amount (USD)": totals.values
        })
        bar_fig = px.bar(bar_data, x="Category", y="Amount (USD)", text="Amount (USD)", title=f"Resource Summary – {selected_country}")
        st.plotly_chart(bar_fig, use_container_width=True)
    st.caption("© 2025 Zichen Zhao. All rights reserved. Use of this app is permitted via authorized access only. Redistribution or reuse of code is prohibited.")

# --- TAB 4: ABOUT ---
with tabs[3]:
    st.header("\U0001F4D8 About This App")
    st.markdown("""
    This assistant supports evidence-based decision-making by making UN INFO 2024 programming data accessible and actionable.

    Developed for the DCO ASG Retreat 2025 to:
    - Analyze sub-output level programming data from 49+ UN Country Teams
    - Cover Youth, Education, Digital, Mining, IFF & Transnational Crime
    - Leverage validated UN INFO datasets (as of April 2025)

    The assistant runs securely using Azure AI and OpenAI o1, all within a private, role-secured environment.

    **Developer:** Zichen Zhao  
    **Email:** ziche.zhao@un.org  
    **Organization:** UN Development Coordination Office (UNDCO)
    """)
    st.caption("© 2025 Zichen Zhao. All rights reserved. Use of this app is permitted via authorized access only. Redistribution or reuse of code is prohibited.")