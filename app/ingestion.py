from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from langchain_core.documents import Document
import validators
import re

def extract_video_id(url:str)->str:
    match =re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})",url)
    ## YT API needs 11 char video ID, not full url
    if match:
        return match.group(1)
    return None

# Validation Functions
def validate_url(url:str)->bool:
    return validators.url(url)

def validate_pdf(file)->bool:
    if file.name.lower().endswith("pdf") and file.size<(10*1024*1024):
        return True
    return False

# Loading functions

def load_youtube(url:str)->list[Document]:
    from langchain_community.document_loaders import YoutubeLoader,UnstructuredURLLoader

    if validate_url(url):
        if "youtube.com" in url or "youtu.be" in url:
            video_id=extract_video_id(url)
            if video_id:
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    
                    transcipt=YouTubeTranscriptApi.get_transcript(video_id)

                    full_text=" ".join([entry["text"] for entry in transcipt])

                    return [Document(page_content=full_text, metadata={"source": url})]
                except (TranscriptsDisabled, NoTranscriptFound):
                    raise ValueError("Transcripts are disabled or not found for this youtube video.")
                except Exception as primary_e:
                    try:
                        from concurrent.futures import ThreadPoolExecutor, TimeoutError

                        with ThreadPoolExecutor(max_workers=1) as executor:
                            loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
                            future = executor.submit(loader.load)
                            return future.result(timeout=10)
                            
                    except TimeoutError:
                        raise ValueError("Failed to fetch transcript: The connection timed out.")
                    except Exception as fallback_e:
                        raise ValueError(f"Failed to fetch YT transcript: {str(fallback_e)}")
        else:
            try:
                loader=UnstructuredURLLoader(urls=[url],ssl_verify=False)
                return loader.load()
            except Exception as e:
                raise ValueError(f"Failed to fetch web content: {str(e)}")
    else:
        return []

def load_pdf(file)->list[Document]:
    import tempfile, os
    from langchain_community.document_loaders import PyPDFLoader


    if validate_pdf(file):
        with tempfile.NamedTemporaryFile(delete=False,
        suffix=".pdf") as temp_file:
            temp_file.write(file.read())
            temp_path=temp_file.name
        
        docs=PyPDFLoader(temp_path).load()
        os.remove(temp_path)
        return docs
    return []
        



    
