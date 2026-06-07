import streamlit as st

def render_evaluation_ui(metrics: dict, source_word_count: int, summary_word_count: int):
    """
    Renders the Streamlit Evaluation UI (Dual-Layer: Executive Summary & Telemetry Expander).
    """
    st.markdown("---")
    
    # assuming 200 words per minute reading speed
    source_reading_time = source_word_count / 200
    summary_reading_time = summary_word_count / 200
    time_saved_mins = max(0.0, source_reading_time - summary_reading_time)
    
    st.subheader("Performance Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="⏱️ Total Generation Time",
            value=f"{metrics.get('end_to_end_latency', 0):.1f}s",
            help="The total time it took for our system to read, process, and summarize your document."
        )
    with col2:
        st.metric(
            label="⏳ Estimated Reading Time Saved",
            value=f"{time_saved_mins:.1f} mins",
            help="An estimate of how much time you saved by reading this summary instead of the original document (based on 200 words per minute)."
        )

   