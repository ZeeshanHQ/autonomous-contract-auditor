from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import time
from app.config import settings

def get_llm(temperature: float = 0.0, provider: str = None):
    """
    Returns an LLM instance based on the provider.
    Default provider is loaded from settings.
    """
    # Small delay to prevent aggressive rate limiting on free tiers
    time.sleep(1.2)
    
    target_provider = provider or settings.LLM_PROVIDER
    
    try:
        if target_provider == "google":
            return ChatGoogleGenerativeAI(
                model=settings.MODEL_NAME,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=temperature,
            )
        elif target_provider == "groq":
            return ChatGroq(
                model=settings.MODEL_NAME if "llama" in settings.MODEL_NAME else "llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
        elif target_provider == "openrouter":
            return ChatOpenAI(
                model=settings.OPENROUTER_MODEL,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=temperature,
                default_headers={
                    "HTTP-Referer": "https://github.com/ZeeshanHQ/autonomous-contract-auditor",
                    "X-Title": "Contract Auditor AI"
                }
            )
        else:
            # Fallback to absolute default if something is wrong
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
    except Exception as e:
        print(f"Error initializing LLM provider {target_provider}: {e}")
        # If primary fails, try to return Groq as the most reliable free backup
        if target_provider != "groq" and settings.GROQ_API_KEY:
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
        raise e
