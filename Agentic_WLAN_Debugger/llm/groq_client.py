# llm/groq_client.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def get_llm(api_key: str):
    return ChatGroq(
        model="groq/compound",
        groq_api_key=api_key,
        temperature=0
    )