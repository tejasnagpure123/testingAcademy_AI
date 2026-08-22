"""
QABuddy.ai — LLM Client
Configurable LLM client supporting both Google Gemini and OpenAI APIs.
Switched via environment variable LLM_PROVIDER.
"""

from typing import List, Dict, Optional
from loguru import logger

from src.config.settings import settings


class LLMClient:
    """
    Unified LLM client supporting Gemini and OpenAI.
    The provider is selected via settings.llm_provider.
    """

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._client = None

        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            # Try new google.genai SDK first; fall back to deprecated google.generativeai
            try:
                from google import genai
                from google.genai import types as genai_types
                client = genai.Client(api_key=settings.gemini_api_key)
                # Wrap in a simple object that matches our .generate_content() call pattern
                self._client = client
                self._gemini_model = settings.gemini_model
                self._genai_types = genai_types
                self._use_new_sdk = True
                logger.info(f"Gemini client initialized (google.genai): {settings.gemini_model}")
            except (ImportError, Exception):
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=settings.gemini_api_key)
                self._client = genai_legacy.GenerativeModel(
                    model_name=settings.gemini_model,
                    generation_config=genai_legacy.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2048,
                        top_p=0.9,
                    ),
                )
                self._use_new_sdk = False
                logger.info(f"Gemini client initialized (google.generativeai): {settings.gemini_model}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini: {e}")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
            logger.info(f"OpenAI client initialized: {settings.openai_model}")
        except ImportError:
            raise ImportError("openai not installed. pip install openai")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI: {e}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System/instructions prompt
            user_prompt: User's prompt with context
            chat_history: Optional previous conversation turns

        Returns:
            Generated response text
        """
        try:
            if self.provider == "gemini":
                return self._generate_gemini(system_prompt, user_prompt, chat_history)
            elif self.provider == "openai":
                return self._generate_openai(system_prompt, user_prompt, chat_history)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"⚠️ Error generating response: {str(e)}"

    def _generate_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate via Gemini API."""
        # Build conversation with system instruction
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        if chat_history:
            history_text = "\n".join(
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in chat_history[-6:]  # Last 6 turns for context
            )
            full_prompt = f"{system_prompt}\n\n## Previous Conversation\n{history_text}\n\n{user_prompt}"

        if self._use_new_sdk:
            # New google.genai SDK: client.models.generate_content(model=..., contents=..., config=...)
            response = self._client.models.generate_content(
                model=self._gemini_model,
                contents=full_prompt,
                config=self._genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    top_p=0.9,
                ),
            )
            return response.text
        else:
            # Legacy google.generativeai SDK: model.generate_content(text)
            response = self._client.generate_content(full_prompt)
            return response.text

    def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate via OpenAI API."""
        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_prompt})

        response = self._client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            top_p=0.9,
        )

        return response.choices[0].message.content
