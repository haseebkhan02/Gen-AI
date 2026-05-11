import streamlit as st
import tempfile
import os
import tempfile
from graph.workflow import build_graph
from utils.visualization import packets_to_df


st.set_page_config(layout="wide")
st.title("📡 Agentic AI WLAN Debugger")


api_key = st.text_input(
    "Enter Groq API Key",
    type="password",
    placeholder="gsk_..."
)

if not api_key:
    st.warning("Please enter your Groq API key to proceed.")
    st.stop()


@st.cache_resource
def get_graph():
    return build_graph()


uploaded_file = st.file_uploader("Upload PCAP", type=["pcap", "pcapng"])


if uploaded_file:
    uploaded_bytes = uploaded_file.getvalue()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pcap")
    tmp.write(uploaded_bytes)
    tmp.flush()
    os.fsync(tmp.fileno())   # 🔥 FORCE write to disk
    tmp.close()

    file_path = tmp.name

    graph = get_graph()

    with st.spinner("Running Agentic AI Workflow..."):
        result = graph.invoke({
            "file_path": file_path,
            "reasoning_steps": [],
            "api_key": api_key
        })

    packets = result.get("packets", [])
    df = packets_to_df(packets)

    st.success("Analysis Complete")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Packet Insights",
        "🧠 Analysis",
        "⚠️ Root Cause",
        "🪜 Reasoning Steps",
        "📈 Throughput"
    ])


    # =========================
    # TAB 1 - PACKET INSIGHTS
    # =========================
    with tab1:

        st.subheader("Packet Timeline")

        if not df.empty:
            timeline = df.groupby("time").size()
            st.line_chart(timeline)

            if "protocol" in df.columns:
                st.subheader("Protocol Distribution")
                st.bar_chart(df["protocol"].value_counts())

            if "src" in df.columns:
                st.subheader("Top Talkers")
                st.bar_chart(df["src"].value_counts().head(10))
        else:
            st.warning("No data")


    # =========================
    # TAB 2 - ANALYSIS
    # =========================
    with tab2:

        st.write(result.get("analysis"))

        st.metric(
            "Anomaly Detected",
            "YES" if result.get("anomaly_detected") else "NO"
        )

        # Optional combined health indicator
        st.metric(
            "System Health Issue",
            "YES" if (
                result.get("anomaly_detected") or
                result.get("throughput_drop")
            ) else "NO"
        )


    # =========================
    # TAB 3 - RCA
    # =========================
    with tab3:

        if result.get("root_cause"):
            st.write(result.get("root_cause"))
        else:
            st.info("RCA skipped (no anomaly)")

        st.subheader("Summary")
        st.write(result.get("summary"))


    # =========================
    # TAB 4 - REASONING TRACE
    # =========================
    with tab4:

        st.subheader("Agent Reasoning Trace")

        steps = result.get("reasoning_steps", [])

        for i, step in enumerate(steps, 1):
            st.markdown(f"**Step {i}:** {step}")


    # =========================
    # TAB 5 - THROUGHPUT (NEW)
    # =========================
    with tab5:

        st.subheader("Throughput Analysis")

        tp_data = result.get("throughput_data", {})

        if tp_data and "mbps" in tp_data:
            st.line_chart(tp_data["mbps"])
        else:
            st.warning("No throughput data available")

        st.metric(
            "Throughput Drop",
            "YES" if result.get("throughput_drop") else "NO"
        )