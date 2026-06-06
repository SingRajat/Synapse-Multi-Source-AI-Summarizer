from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.llm import get_llm
from langchain_core.documents import Document
from app.prompts import map_prompt, refine_prompt
import time

def split_docs(docs)->list[Document]:
    splitter=RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=200)
    chunks=splitter.split_documents(docs)
    return chunks

def map_summaries(chunks,llm)->list[str]:
    summaries=[]
    for chunk in chunks:
        summary=map_prompt.format(text= chunk.page_content) 
        # format() user keyword arguments, not a dict
        response=llm.invoke(summary)
        summaries.append(response.content)

        time.sleep(2)
    return summaries

def refine_summaries(summaries: list[str],llm)->str:
    refined=summaries[0] 
    for summary in summaries[1:]:
        prompt_text= refine_prompt.format(
            existing_summary=refined,
            new_summary=summary
        )
        response=llm.invoke(prompt_text)
        refined=response.content
    return refined

def generate_summary(docs: list[Document], api_key:str)->str:
    llm=get_llm(api_key=api_key)
    chunks=split_docs(docs)

    if not chunks:
        return "No content found to summarize."
    
    summaries= map_summaries(chunks,llm)

    if len(summaries)==1:
        return summaries[0]
    
    final_summary=refine_summaries(summaries,llm)
    return final_summary