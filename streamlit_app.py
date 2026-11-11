import streamlit as st
import pandas as pd

from src.toronto_data import load_toronto_311, prepare_data, get_dataset_resources
from src.chat_logic import classify_message, build_reply

st.set_page_config(page_title="Toronto 311 Assistant", page_icon="🏙️", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1120px; padding-top: 1.4rem;}
.hero {background:linear-gradient(115deg,#12344d,#1f6687);padding:1.5rem 1.7rem;border-radius:18px;color:white;margin-bottom:1rem;}
.hero h1 {font-size:2rem;margin:0 0 .35rem 0;}
.hero p {color:#e5eff6;margin:0;}
div[data-testid="stChatMessage"] {border-radius:14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=86400, show_spinner=False)
def get_data():
    raw, metadata = load_toronto_311()
    return prepare_data(raw), metadata

st.sidebar.title("🏙️ Toronto 311")
page = st.sidebar.radio("Explore", ["Chat with 311", "Browse service types", "Explore 311 data", "About & data notes"])
st.sidebar.caption("Student prototype · Not an official City service")
st.sidebar.warning("For emergencies, call 911.")

try:
    with st.spinner("Connecting to Toronto Open Data…"):
        df, metadata = get_data()
    data_ok = not df.empty
except Exception as exc:
    df, metadata, data_ok = pd.DataFrame(), {}, False
    st.sidebar.error("Toronto dataset could not be loaded.")
    st.sidebar.caption(str(exc)[:240])

if data_ok:
    st.sidebar.success(f"Dataset connected · {len(df):,} rows")
    st.sidebar.caption(f"Source: {metadata.get('resource_name', 'Toronto Open Data')}")
else:
    st.sidebar.info("You can still explore the interface, but live dataset features are unavailable until the data connection works.")

if page == "Chat with 311":
    st.markdown("""
    <div class="hero">
      <h1>How can we help you today?</h1>
      <p>Tell me what is happening. I can help identify a likely Toronto service request type.</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("This prototype uses historical public 311 records to inform service categories. It does not create a real City request.")
    quick = st.columns(4)
    examples = [
        ("🕳️ Road issue", "There is a pothole on my street."),
        ("🌳 Tree issue", "A tree branch needs pruning."),
        ("🗑️ Waste", "My garbage was not collected."),
        ("🔊 Noise", "There is construction noise at night."),
    ]
    for col, (label, message) in zip(quick, examples):
        if col.button(label, use_container_width=True):
            st.session_state["prompt_next"] = message

    if "chat" not in st.session_state:
        st.session_state.chat = [{
            "role": "assistant",
            "content": "Hi! Describe the municipal issue and, if comfortable, include the nearest intersection or general area. Please don't share names, phone numbers, or other personal information."
        }]
    for item in st.session_state.chat:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    user_text = st.chat_input("Describe your issue…")
    if "prompt_next" in st.session_state:
        user_text = st.session_state.pop("prompt_next")

    if user_text:
        st.session_state.chat.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        classification = classify_message(user_text, df if data_ok else None)
        answer = build_reply(user_text, classification, df if data_ok else None)
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})

        if classification.get("service_type"):
            with st.expander("See the data behind this suggestion"):
                st.write("**Suggested historical service type:**", classification["service_type"])
                st.write("**Division in historical data:**", classification.get("division", "Not available"))
                st.write("**Classification method:**", classification.get("method", "keyword baseline"))
                st.caption("This is a suggested category, not an official determination or a live service request.")

    if st.button("Start a new conversation"):
        st.session_state.chat = []
        st.rerun()

elif page == "Browse service types":
    st.title("Browse Toronto 311 service types")
    st.write("Explore the actual service types and divisions present in the published dataset.")
    if data_ok:
        type_col = "service_type"
        division_col = "division"
        search = st.text_input("Search service types", placeholder="e.g. pruning, pothole, noise")
        options = sorted(df[type_col].dropna().astype(str).unique())
        if search:
            options = [x for x in options if search.lower() in x.lower()]
        st.write(f"**{len(options):,} matching service types**")
        view = df[df[type_col].isin(options)]
        summary = (view.groupby([type_col, division_col], dropna=False)
                   .size().reset_index(name="historical_records")
                   .sort_values("historical_records", ascending=False))
        st.dataframe(summary.head(300), use_container_width=True, hide_index=True)
    else:
        st.warning("Dataset is not available. Check the data connection or try again later.")

elif page == "Explore 311 data":
    st.title("Explore Toronto 311 historical requests")
    if data_ok:
        d = df.copy()
        c1, c2, c3 = st.columns(3)
        c1.metric("Records loaded", f"{len(d):,}")
        c2.metric("Service types", f"{d['service_type'].nunique():,}")
        c3.metric("Divisions", f"{d['division'].nunique():,}")

        if "created" in d and d["created"].notna().any():
            d["year"] = d["created"].dt.year
            yearly = d.groupby("year").size().sort_index()
            st.subheader("Requests by year")
            st.bar_chart(yearly)

        st.subheader("Most common recorded service types")
        top = d["service_type"].value_counts().head(15)
        st.bar_chart(top)

        st.subheader("Requests by division")
        st.bar_chart(d["division"].value_counts())

        st.subheader("Request status distribution")
        st.bar_chart(d["status"].fillna("Unknown").value_counts())

        st.caption("Counts describe the records loaded from the selected published resource. They are not a measure of all 311 contacts or all City work.")
    else:
        st.warning("Dataset is not available. Check the data connection or try again later.")

elif page == "About & data notes":
    st.title("About this prototype")
    st.markdown("""
**What this app does**
- Loads Toronto's public 311 Customer-Initiated Service Requests dataset.
- Uses the published service-type vocabulary to suggest a likely request category.
- Shows historical service-type, division and status patterns.
- Demonstrates a chat-first interface for a future guided intake workflow.

**What this app does not do**
- It does not submit requests to the City.
- It does not check the live status of a resident's request.
- It does not know whether a specific issue has already been reported.
- It does not provide official service standards or promise response times.

**Important data limitation**
The historical dataset contains structured request attributes, not the original free-text resident descriptions. Natural-language examples for model training must therefore be synthetic and labelled against reviewed Toronto service types.

**Privacy**
Use synthetic examples for testing. Do not enter real personal information.
""")
    st.markdown("[Toronto Open Data: 311 Service Requests – Customer Initiated](https://open.toronto.ca/dataset/311-service-requests-customer-initiated/)")
    st.markdown("[Official Toronto 311 service information](https://www.toronto.ca/home/311-toronto-at-your-service/)")
