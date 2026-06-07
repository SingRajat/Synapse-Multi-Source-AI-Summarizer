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

  
    with st.expander("⚙️ System Telemetry & Profiling"):
        st.markdown("#### Context Window Utilization")
        
        total_tokens = metrics.get('total_tokens', 0)
        context_window = metrics.get('context_window', 131072)
        utilization = min(1.0, total_tokens / context_window) if context_window > 0 else 0.0
        
        # Color gradient based on utilization
        color = "#28a745" # Green
        if utilization > 0.8:
            color = "#dc3545" # Red
        elif utilization > 0.6:
            color = "#ffc107" # Yellow
            
        st.markdown(
            f"""
            <div style="width: 100%; background-color: #333; border-radius: 5px; margin-bottom: 5px;">
              <div style="width: {max(utilization * 100, 1):.1f}%; background-color: {color}; height: 18px; border-radius: 5px;"></div>
            </div>
            <p style="text-align: right; font-size: 0.85em; color: #a0a0a0; margin-top: 0px;">
              {total_tokens:,} / {context_window:,} tokens ({utilization * 100:.1f}%)
            </p>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Bottleneck Analysis")
        
        bottleneck_stage = metrics.get('bottleneck_stage', 'Unknown')
        bottleneck_pct = metrics.get('bottleneck_percentage', 0.0)
        
        st.warning(f"**⚠ Bottleneck Detected**  \n**Stage:** {bottleneck_stage}  \n**Contribution:** {bottleneck_pct}% of total latency")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Latency Waterfall")
        
        try:
            import plotly.graph_objects as go
            stages = ["Ingest", "Chunk", "Map", "Reduce", "Overhead"]
            
            ingest = metrics.get("ingest_latency", 0)
            chunk = metrics.get("chunk_latency", 0)
            map_l = metrics.get("map_latency", 0)
            reduce_l = metrics.get("reduce_latency", 0)
            total = metrics.get("end_to_end_latency", 0)
            overhead = max(0.0, total - (ingest + chunk + map_l + reduce_l))
            
            x_data = [ingest, chunk, map_l, reduce_l, overhead]
            
            # Sleek, premium gradient-like color palette
            colors = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#475569"]
            
            fig = go.Figure()
            for stage, val, color in zip(stages, x_data, colors):
                fig.add_trace(go.Bar(
                    y=["Latency"],
                    x=[val],
                    name=stage,
                    orientation='h',
                    marker=dict(
                        color=color,
                        line=dict(width=0) # Remove rigid borders
                    ),
                    text=f"{val:.1f}s",
                    textposition='inside',
                    textfont=dict(color='white', size=13),
                    hoverinfo="name+x"
                ))
            
            fig.update_layout(
                barmode='stack',
                height=180, # More compact
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title="", 
                    showgrid=False, # Remove rigid gridlines
                    zeroline=False,
                    showticklabels=False # Clean minimalist look
                ),
                yaxis=dict(visible=False, showgrid=False, zeroline=False),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.1, 
                    xanchor="center", 
                    x=0.5,
                    font=dict(size=13, color="gray")
                )
            )
            
            # Disable the plotly modebar for a cleaner look
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        except ImportError:
            st.info("💡 Plotly is not installed. Please run `pip install plotly` to see the latency waterfall chart.")
