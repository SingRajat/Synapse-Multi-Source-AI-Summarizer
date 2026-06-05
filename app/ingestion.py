from langchain_community.document_loaders import PyPDFLoader,YoutubeLoader,UnstructuredURLLoader
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import validators, os, tempfile

# Validation Functions
def validate_url(url:str)->bool:
    return validators.url(url)

def validate_pdf(file)->bool:
    if file.name.endswith("pdf") and file.size<(10*1024*1024):
        return True
    return False

# Loading functions

def load_youtube(url:str)->list[Document]:
    if validate_url(url):
        if "youtube.com" in url or "youtube.be" in url:
            try:
                loader=YoutubeLoader.from_youtube_url(url,add_video_info=True)
                return loader.load()
            except (TranscriptsDisabled,NoTranscriptFound):
                raise ValueError(f"Transcripts are disabled or not found for this youtube video.")
            except Exception as e:
                raise ValueError(f"Failed to fetch YT transcript: {str(e)}")
        else:
            try:
                loader=UnstructuredURLLoader(urls=[url],ssl_verify=False)
                return loader.load()
            except Exception as e:
                raise ValueError(f"Failed to fetch web content: {str(e)}")
    else:
        return []

def load_pdf(file)->list[Document]:
    if validate_pdf(file):
        with tempfile.NamedTemporaryFile(delete=False,
        suffix=".pdf") as temp_file:
            temp_file.write(file.read())
            temp_path=temp_file.name
        
        loader=PyPDFLoader(temp_path)
        docs=loader.load()
        os.remove(temp_path)
        return docs
    return []
        



    
