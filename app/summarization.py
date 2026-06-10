from app.prompts import map_prompt
from langchain_core.documents import Document
import asyncio
import time

def split_docs(docs)->list[Document]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter=RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=200)
    chunks=splitter.split_documents(docs)
    return chunks

async def async_map_summaries(chunks, llm, semaphore_limit=5):

    semaphore=asyncio.Semaphore(semaphore_limit)

    async def process_chunk(chunk):
        async with semaphore:
            prompt=map_prompt.format(text=chunk.page_content)
            response=await llm.ainvoke(prompt)

            usage =response.response_metadata.get("token_usage", {})
            inp=usage.get("prompt_tokens", 0)
            out=usage.get("completion_tokens", 0)
            return response.content, inp, out
    
    results= await asyncio.gather(*[process_chunk(c) for c in chunks])
    summaries=[r[0] for r in results]
    input_tokens=sum(r[1] for r in results)
    output_tokens=sum(r[2] for r in results)

    return summaries, input_tokens, output_tokens


def refine_summaries(summaries: list[str],llm, on_token=None):
    from app.prompts import  refine_prompt

    refined=summaries[0] 
    input_tokens = 0
    output_tokens = 0
    for i,summary in enumerate(summaries[1:]):
        prompt_text= refine_prompt.format(
            existing_summary=refined,
            new_summary=summary
        )

        is_last= (i == len(summaries)-2)
        if is_last and on_token:
            full_response=""
            last_metadata={}
            for chunk in llm.stream(prompt_text):
                token= chunk.content
                if token:
                    full_response+=token
                    on_token(token)
                if chunk.response_metadata:
                    last_metadata=chunk.response_metadata
            refined=full_response
            usage = last_metadata.get("token_usage", {})
            input_tokens += usage.get("prompt_tokens", 0)
            output_tokens += usage.get("completion_tokens", 0)
        else:
            response=llm.invoke(prompt_text)
            refined=response.content
            
            usage = response.response_metadata.get("token_usage", {})
            input_tokens += usage.get("prompt_tokens", 0)
            output_tokens += usage.get("completion_tokens", 0)
        
    return refined, input_tokens, output_tokens

def generate_summary(docs: list[Document], api_key:str, on_token=None)->tuple[str, dict]:
    from app.llm import get_llm
    
    metrics = {
        "chunk_count": 0,
        "map_input_tokens": 0,
        "map_output_tokens": 0,
        "reduce_input_tokens": 0,
        "reduce_output_tokens": 0,
        "chunk_latency": 0.0,
        "map_latency": 0.0,
        "reduce_latency": 0.0,
    }

    llm=get_llm(api_key=api_key)
    
    t0 = time.time()
    chunks=split_docs(docs)
    metrics["chunk_latency"] = round(time.time() - t0, 4)
    metrics["chunk_count"] = len(chunks)

    if not chunks:
        return "No content found to summarize.", metrics
    
    t1 = time.time()
    summaries, map_in, map_out = asyncio.run(async_map_summaries(chunks,llm))
    metrics["map_latency"] = round(time.time() - t1, 4)
    metrics["map_input_tokens"] = map_in
    metrics["map_output_tokens"] = map_out

    if len(summaries)==1:
        return summaries[0], metrics
    
    t2 = time.time()
    final_summary, reduce_in, reduce_out = refine_summaries(summaries,llm,on_token=on_token)
    metrics["reduce_latency"] = round(time.time() - t2, 4)
    metrics["reduce_input_tokens"] = reduce_in
    metrics["reduce_output_tokens"] = reduce_out
    
    return final_summary, metrics