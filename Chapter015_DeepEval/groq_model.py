import os
from pathlib import Path

from deepeval.models import OpenAIModel
from dotenv import load_dotenv

PROJECT_ENV = Path(__file__).resolve().with_name(".env")


def create_groq_evaluation_model() -> OpenAIModel:
    load_dotenv(PROJECT_ENV)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GROQ_API_KEY in Chapter015_DeepEval/.env or the environment."
        )

    return OpenAIModel(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=api_key,
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        temperature=0,
    )
