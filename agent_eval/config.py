import os
from openai import AsyncOpenAI
from strands.models.openai import OpenAIModel


def create_model():
    """Create the model - easily swappable for different providers.

    Environment variables:
        OPENAI_BASE_URL: URL for OpenAI-compatible API (default: http://127.0.0.1:4000/v1)
        OPENAI_API_KEY: API key (default: not-needed for local models)
        MODEL_ID: Model name to use (default: llama3)
    """
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "NA"),
        base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:4000/v1"),
    )

    return OpenAIModel(
        client=client,
        # model_id=os.getenv("MODEL_ID", "nemotron-3-super-120b-a12b"),
        model_id=os.getenv("EVAL_MODEL_ID", "local-vllm"),
    )


def create_eval_model():
    """Create model for eval judges (LLM-as-judge).

    Environment variables:
        EVAL_MODEL_BASE_URL: URL for OpenAI-compatible API (default: same as OPENAI_BASE_URL)
        EVAL_MODEL_API_KEY: API key (default: same as OPENAI_API_KEY)
        EVAL_MODEL_ID: Model name for judge (default: minimax-m2.7)
    """
    client = AsyncOpenAI(
        api_key=os.getenv("EVAL_MODEL_API_KEY", os.getenv("OPENAI_API_KEY", "NA")),
        base_url=os.getenv("EVAL_MODEL_BASE_URL", os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:4000/v1")),
    )

    return OpenAIModel(
        client=client,
        # model_id=os.getenv("EVAL_MODEL_ID", "minimax-m2.7"),
        model_id=os.getenv("EVAL_MODEL_ID", "local-vllm"),
    )
