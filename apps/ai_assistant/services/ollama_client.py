# apps/ai_assistant/services/ollama_client.py
"""
Ollama LLM client for the Vendora AI Assistant.
Handles model warmup, JSON generation, classification, and context-aware generation.
"""

import json
import logging
import time
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (
            base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_MODEL", "qwen2.5:3b")
        # Keep timeout reasonable (default 15s) so the chatbot never hangs the user
        # Allow enough time for Qwen 2.5 3B running on CPU
        configured_timeout = getattr(settings, "OLLAMA_TIMEOUT", 60)
        self.timeout = timeout or configured_timeout
        self._warmed_up = False
        self._circuit_broken_until = 0.0

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is tripped due to recent failure/timeout."""
        return time.time() < self._circuit_broken_until

    def trip_circuit(self, duration_seconds: int = 60):
        """Trip circuit breaker to prevent repeated timeouts."""
        self._circuit_broken_until = time.time() + duration_seconds
        logger.warning(f"Ollama circuit breaker tripped for {duration_seconds}s")

    # ─── Warmup ───
    def _ensure_warm(self):
        """Quick health-check probe to verify Ollama is alive without heavy blocking."""
        if self._warmed_up or self.is_circuit_open():
            return

        try:
            # Fast ping (2s timeout) to see if server is responsive
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                self._warmed_up = True
            else:
                self.trip_circuit(30)
        except Exception as e:
            logger.warning(f"Ollama unreachable: {e}")
            self.trip_circuit(45)

    # ─── Core generation ───
    def _post_generate(self, prompt, format_json=True, options=None, max_retries=1):
        """Generate with circuit breaker protection and reasonable timeout."""
        if self.is_circuit_open():
            raise OllamaClientError("Ollama circuit breaker is currently active (service down or slow).")

        self._ensure_warm()
        if self.is_circuit_open():
            raise OllamaClientError("Ollama service unreachable.")

        default_options = {
            "temperature": 0.3,
            "num_predict": 100,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        }
        if options:
            default_options.update(options)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": default_options,
        }
        if format_json:
            payload["format"] = "json"

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                elapsed = time.time() - start_time
                logger.debug(f"Ollama response in {elapsed:.2f}s")

                text = (data.get("response") or "").strip()
                if not text:
                    raise OllamaClientError("Ollama returned an empty response.")

                if format_json:
                    try:
                        json.loads(text)
                        return text
                    except json.JSONDecodeError:
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            try:
                                json.loads(json_match.group())
                                return json_match.group()
                            except json.JSONDecodeError:
                                pass
                        return json.dumps({"reply": text, "product_ids": []})

                return text

            except requests.Timeout:
                logger.warning(f"Ollama request timed out after {self.timeout}s")
                self.trip_circuit(60)  # Trip circuit breaker for 60 seconds
                raise OllamaClientError("Request timed out. Falling back to local search.")

            except requests.RequestException as exc:
                logger.warning(f"Ollama request failed: {exc}")
                self.trip_circuit(45)
                raise OllamaClientError(f"Ollama error: {exc}")

    # ─── Conversation JSON generation ────────────────────────────────────────
    def generate_conversation_json(self, user_message, chat_history, runtime_context):
        """Generate a conversation response as JSON with product_ids."""
        try:
            prompt = f"""You are Vendora, a friendly shopping assistant.
Keep responses short, warm, and conversational.
Never invent product names or prices — only use data from the context.

User: {user_message[:200]}
Context: {runtime_context[:500] if runtime_context else "Shopping assistant"}

Response JSON: {{"reply": "...", "product_ids": []}}"""

            raw = self._post_generate(
                prompt=prompt,
                format_json=True,
                options={"temperature": 0.4, "num_predict": 100},
            )
            parsed = json.loads(raw)

            product_ids = parsed.get("product_ids", [])
            if not isinstance(product_ids, list):
                product_ids = []
            product_ids = [int(pid) for pid in product_ids if str(pid).isdigit()][:5]

            return {
                "reply": (parsed.get("reply") or "Hello! 👋 How can I help you?").strip(),
                "product_ids": product_ids,
                "raw": parsed,
            }
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return {
                "reply": "Hello! 👋 How can I help you shop today?",
                "product_ids": [],
            }

    # ─── Classification (was missing — fixes ai_agent.py and intent_classifier.py) ───
    def classify_with_prompt(self, prompt: str) -> str:
        """
        Run a classification/analysis prompt and return the raw JSON string.
        Used by ai_agent.py for query analysis and intent_classifier.py for
        ambiguous intent classification.
        """
        try:
            return self._post_generate(
                prompt=prompt,
                format_json=True,
                options={"temperature": 0.1, "num_predict": 150},
            )
        except OllamaClientError as e:
            logger.warning(f"Classification failed: {e}")
            raise

    # ─── RAG-style grounded generation ───────────────────────────────────────
    def generate_with_context(
        self,
        system_prompt: str,
        user_message: str,
        context: str,
        chat_history: list = None,
        temperature: float = 0.3,
        max_tokens: int = 150,
    ) -> dict:
        """
        Generate a grounded response using system prompt + retrieved context.
        This is the main RAG generation method.

        Args:
            system_prompt: The persona/system instructions.
            user_message: The user's current message.
            context: Retrieved product data and other context.
            chat_history: Recent conversation history.
            temperature: LLM temperature (lower = more factual).
            max_tokens: Maximum tokens to generate.

        Returns:
            {"reply": str, "product_ids": list}
        """
        try:
            # Build history context string
            history_text = ""
            if chat_history:
                recent = chat_history[-6:]  # Last 3 turns
                for msg in recent:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:100]
                    history_text += f"{role.capitalize()}: {content}\n"

            prompt = f"""{system_prompt}

{context}

{f"RECENT CONVERSATION:{chr(10)}{history_text}" if history_text else ""}

USER MESSAGE: {user_message[:300]}

Respond naturally using ONLY the product data provided above. Never invent products.
Response JSON: {{"reply": "your response here", "product_ids": [list of product IDs mentioned]}}"""

            raw = self._post_generate(
                prompt=prompt,
                format_json=True,
                options={"temperature": temperature, "num_predict": max_tokens},
            )
            parsed = json.loads(raw)

            product_ids = parsed.get("product_ids", [])
            if not isinstance(product_ids, list):
                product_ids = []
            product_ids = [int(pid) for pid in product_ids if str(pid).isdigit()][:5]

            reply = (parsed.get("reply") or "").strip()
            if not reply:
                reply = "I'd be happy to help! Could you tell me more about what you're looking for?"

            return {"reply": reply, "product_ids": product_ids}

        except Exception as e:
            logger.error(f"Context generation error: {e}")
            return {
                "reply": "I'd love to help you find something! What are you looking for?",
                "product_ids": [],
            }

    # ─── Health check ────────────────────────────────────────────────────────
    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False