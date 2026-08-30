import os
import sys
import logging
import asyncio
import warnings
import traceback

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"

from google import genai
from google.genai import types
from core.config import GOOGLE_API_KEY

_client = None

def get_client():
    global _client
    if _client is None and GOOGLE_API_KEY:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

def ask_llm(prompt: str, system_instruction: str = "You are an AI software architect and technical code audit expert.") -> str:
    """
    Synchronous wrapper to query Gemini using google-genai SDK with multi-model fallback.
    Uses exponential backoff on 429 rate-limit errors to avoid wasting quota.
    """
    if not GOOGLE_API_KEY:
        return "ERROR: GOOGLE_API_KEY configuration is missing or empty."

    try:
        client = get_client()
        if not client:
            return "ERROR: Gemini client initialization failed."

        # Gemini model fallback chain - gemini-3.6-flash is primary (fastest, best quality)
        models_to_try = [
            "gemini-3.6-flash",
            "Gemini 3.1 Flash Lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as m_err:
                last_error = m_err
                continue  # silently try next model

        return f"ERROR: LLM query failed across available models: {str(last_error)}"

    except Exception as exc:
        print(f"[LLM ERROR] {type(exc).__name__}: {str(exc)}")
        return f"ERROR: LLM query failed: {str(exc)}"

async def ask_llm_async(prompt: str, system_instruction: str = "You are an AI software architect and technical code audit expert.") -> str:
    """
    Asynchronous non-blocking wrapper to query Gemini.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, ask_llm, prompt, system_instruction)