from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq

load_dotenv()

def get_llm(api_key: str=None,
            model_name: str="llama-3.3-70b-versatile",
            temperature:float=0.4)-> ChatGroq:
            
            if api_key is None:
                api_key=os.getenv("GROQ_API_KEY")
            if not api_key:
                print("GROQ api is required")
            return ChatGroq(
                api_key=api_key,
                model=model_name,
                temperature=temperature,
            )