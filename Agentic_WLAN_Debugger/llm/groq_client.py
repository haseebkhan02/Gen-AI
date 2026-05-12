# llm/groq_client.py

import os
from langchain_groq import ChatGroq

def get_llm(api_key: str):
    return ChatGroq(
        model="openai/gpt-oss-120b",
        groq_api_key=api_key,
        temperature=0
    )
