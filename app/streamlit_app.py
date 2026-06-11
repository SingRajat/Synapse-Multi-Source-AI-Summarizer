import validators
import streamlit as st
import sys
import os
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

## Streamlit APP

st.set_page_config(page_title="Summarize text from YT/Websites/PDFs")
st.title("Summarize text from YT/Websites/PDFs")
st.subheader('Summarize URL')

if "summary" not in st.session_state:
    st.session_state["summary"] =""

with st.sidebar:
    groq_api_key=st.text_input("Groq API Key", value="", type="password")

summary_mode = st.sidebar.selectbox(
    "Select Summary Mode",
    ["Detailed", "Quick", "Technical", "ELI5"],
    index=0
)

@st.cache_data(show_spinner="Fetching and processing URL content...")
def get_url_content(url:str):
    """Caches document ingestion for web and youtube URLs."""
    from app.ingestion import load_youtube
    return load_youtube(url)

@st.cache_data(show_spinner="Extracting text from PDF...")
def get_pdf_content(file_name: str, file_bytes:bytes):
    """Caches PDF parsing"""
    from app.ingestion import load_pdf
    
    class MockFile:
        name=file_name
        size=len(file_bytes)
        def read(self): return file_bytes
    return load_pdf(MockFile())

    


url=st.text_input("Enter URL", label_visibility="collapsed",
                 value="", placeholder="https://....")

uploaded_file=st.file_uploader("or upload a PDF", type=["pdf"])

if st.button("Summarize the content"):
    if not groq_api_key.strip():
        st.warning("Please provide your GROQ API key")
    elif not url.strip() and not uploaded_file:
        st.warning("Please provide a url or upload a PDF.")
    else:
        try:
            import time
            from app.benchmark import create_default_metrics, save_to_csv
            metrics = create_default_metrics()
            e2e_start = time.time()
            
            ingest_start = time.time()
            if uploaded_file:
                metrics["source_type"] = "pdf"
                metrics["source_name"] = uploaded_file.name
                doc=get_pdf_content(uploaded_file.name,uploaded_file.read())
            elif url.strip():
                if not validators.url(url):
                    st.error("Please enter a valid url.")
                    st.stop()
                metrics["source_name"] = url
                if "youtube.com" in url or "youtu.be" in url:
                    metrics["source_type"] = "youtube"
                else:
                    metrics["source_type"] = "website"
                doc=get_url_content(url)
            
            metrics["ingest_latency"] = round(time.time() - ingest_start, 4)

            if not doc:
                st.error("No content could be extracted.")
                st.stop()
            
            doc_content=tuple(d.page_content for d in doc)
            
            # Calculate source word count manually since it's no longer in the CSV schema
            full_text = " ".join(doc_content)
            source_word_count = len(full_text.split())

            cache_string=f"{doc_content}_{summary_mode}_llama-3.3-70b-8192"

            cache_key="summary_" + hashlib.sha256(str(cache_string).encode()).hexdigest()[:16]

            if cache_key in st.session_state:
                summary, pipe_metrics =st.session_state[cache_key]
                st.session_state["summary"]=summary
            else:
                from app.summarization import generate_summary
                from langchain_core.documents import Document
                docs=[Document(page_content=content) for content in doc_content]

                stream_container=st.empty()
                stream_container.info("Analyzing and summarizing content....")
                stream_state={"text": "", "first": True}
                def on_token(token):
                    if stream_state["first"]:
                        stream_container.empty()
                        stream_state["first"]=False
                    stream_state["text"]+=token
                    stream_container.markdown(stream_state["text"])
                summary, pipe_metrics = generate_summary(docs, groq_api_key, 
                                                        mode=summary_mode,
                                                        on_token=on_token)
                stream_container.empty()

                st.session_state[cache_key]=(summary, pipe_metrics)
                st.session_state["summary"]=summary
            
            # Merge pipeline metrics
            for k, v in pipe_metrics.items():
                metrics[k] = v
                
            metrics["input_tokens"] = metrics["map_input_tokens"] + metrics["reduce_input_tokens"]
            metrics["output_tokens"] = metrics["map_output_tokens"] + metrics["reduce_output_tokens"]
            metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
            
            metrics["end_to_end_latency"] = round(time.time() - e2e_start, 4)
            metrics["success"] = True
            
            
            is_cache_hit = metrics["end_to_end_latency"] < metrics.get("map_latency", 0)
            
            if is_cache_hit:
                metrics["ingest_latency"] = 0.0
                metrics["chunk_latency"] = 0.0
                metrics["map_latency"] = 0.0
                metrics["reduce_latency"] = 0.0
                metrics["bottleneck_stage"] = "Cache Hit (Instant)"
                metrics["bottleneck_percentage"] = 0.0
            else:
                stages = {
                    "Ingest": metrics.get("ingest_latency", 0.0),
                    "Chunk": metrics.get("chunk_latency", 0.0),
                    "Map": metrics.get("map_latency", 0.0),
                    "Reduce": metrics.get("reduce_latency", 0.0)
                }
                bottleneck_stage = max(stages, key=stages.get)
                max_latency = stages[bottleneck_stage]
                
                bottleneck_pct = 0.0
                if metrics["end_to_end_latency"] > 0:
                    bottleneck_pct = round((max_latency / metrics["end_to_end_latency"]) * 100, 2)
                    
                metrics["bottleneck_stage"] = bottleneck_stage
                metrics["bottleneck_percentage"] = bottleneck_pct
            
            save_to_csv(metrics)
            
            # Store in session state for rendering the UI
            st.session_state["metrics"] = metrics
            st.session_state["source_word_count"] = source_word_count
            
            st.info("Metrics successfully logged to benchmarks/baseline_v3.csv")
            
        except ValueError as e:
            st.error(str(e))
        except PermissionError:
            st.error("⚠️ **Permission Denied:** Could not save metrics to the CSV file because it is currently open in another program (like Excel). Please close the CSV file and click Summarize again.")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate_limit_exceeded" in error_msg:
                # Log the rate limit failure to CSV
                metrics["success"] = False
                metrics["error_type"] = "rate_limit_exceeded"
                metrics["rate_limit_hits"] += 1
                if 'e2e_start' in locals():
                    metrics["end_to_end_latency"] = round(time.time() - e2e_start, 4)
                save_to_csv(metrics)
                
                # Extract wait time from Groq error message
                import re
                match = re.search(r"Please try again in ([a-zA-Z0-9.]+s)", error_msg)
                wait_time = match.group(1) if match else "a few minutes"
                
                st.error(f"⚠️ **Token Limit Exceeded:** You have reached the Groq Free Tier API limits. Please try again in **{wait_time}**.")
            else:
                st.error(f"An unexpected error occured: {error_msg}")

if st.session_state.get("summary"):
    st.success("Summary generated!")
    st.markdown(st.session_state["summary"])
    
    # Render the Evaluation UI
    from app.evaluation import render_evaluation_ui
    summary_word_count = len(st.session_state["summary"].split())
    if "metrics" in st.session_state and "source_word_count" in st.session_state:
        render_evaluation_ui(
            metrics=st.session_state["metrics"],
            source_word_count=st.session_state["source_word_count"],
            summary_word_count=summary_word_count
        )