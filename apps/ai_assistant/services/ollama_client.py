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
    def __init__(self, base_url=None, model=None, timeout=30):
        self.base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        # Use tinyllama as default (lightweight model)
        self.model = model or getattr(settings, "OLLAMA_MODEL", "tinyllama")
        self.timeout = timeout
        self._warmed_up = False
        
    def _ensure_warm(self):
        """Warm up the model if not already loaded"""
        if not self._warmed_up:
            try:
                print("🔄 Warming up TinyLlama model...")
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": "Hello",
                        "stream": False,
                        "options": {"num_predict": 5}
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    self._warmed_up = True
                    print("✅ Model warmed up successfully")
                else:
                    print("⚠️ Model warmup failed")
            except Exception as e:
                print(f"⚠️ Model warmup error: {e}")

    def _post_generate(self, prompt, format_json=True, options=None, max_retries=2):
        """Generate with retry logic and timeout - optimized for TinyLlama"""
        
        # Warm up if not done
        if not self._warmed_up:
            self._ensure_warm()
            
        # Optimized options for TinyLlama
# In _post_generate method, update default_options:
        default_options = {
            "temperature": 0.3,
            "num_predict": 60,  # Reduced from 100 for faster responses
            "top_k": 30,
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
                print(f"⏳ Sending to {self.model}...")
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                elapsed = time.time() - start_time
                print(f"⏱️ Response in {elapsed:.2f}s")
                
                text = (data.get("response") or "").strip()
                if not text:
                    if attempt < max_retries - 1:
                        continue
                    raise OllamaClientError("Ollama returned an empty response.")
                    
                # If we need JSON format, validate it
                if format_json:
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(text)
                        return text
                    except json.JSONDecodeError:
                        # Try to extract JSON from the response
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            try:
                                json.loads(json_match.group())
                                return json_match.group()
                            except:
                                pass
                        # If not valid JSON, wrap it in a JSON object
                        print(f"⚠️ Response not valid JSON, wrapping it")
                        fallback = json.dumps({"response": text, "product_ids": []})
                        return fallback
                
                return text
                
            except requests.Timeout:
                print(f"⚠️ Timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise OllamaClientError("Request timed out. Please try again.")
            except requests.RequestException as exc:
                print(f"❌ Request error: {exc}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise OllamaClientError(f"Ollama error: {exc}")

    def classify_intent(self, message, history):
        """Classify intent with optimized prompts for TinyLlama"""
        
        # Quick classification first (instant)
        quick_result = self._quick_classify(message)
        
        # If it's a simple intent, return immediately
        if quick_result["intent"] in ["SHOW_CATEGORIES", "SHOW_FEATURED", "CHITCHAT"]:
            print(f"⚡ Quick classification: {quick_result['intent']}")
            return quick_result
        
        # Use TinyLlama for complex queries
        try:
            print("🧠 Classifying with TinyLlama...")
            
            # Short, clear prompt for TinyLlama
            prompt = f"""Classify this shopping message.
Options: SEARCH_PRODUCTS, ASK_CLARIFICATION, UNKNOWN.
If product mentioned → SEARCH_PRODUCTS.
If vague shopping → ASK_CLARIFICATION.
Else → UNKNOWN.
Return ONLY JSON: {{"intent":"...","keyword":"..."}}

Message: {message[:100]}
JSON:"""
            
            raw = self._post_generate(
                prompt=prompt, 
                format_json=True, 
                options={"temperature": 0.1, "num_predict": 50}
            )
            print(f"📝 Raw: {raw}")
            parsed = json.loads(raw)
            print(f"✅ Parsed: {parsed}")
            
            intent = (parsed.get("intent") or "UNKNOWN").upper()
            # Map to valid intents
            if intent not in ["SEARCH_PRODUCTS", "ASK_CLARIFICATION", "UNKNOWN"]:
                if "search" in intent.lower() or "product" in intent.lower():
                    intent = "SEARCH_PRODUCTS"
                else:
                    intent = "UNKNOWN"
            
            return {
                "intent": intent,
                "keyword": (parsed.get("keyword") or message)[:50],
                "category_hint": (parsed.get("category_hint") or "").strip(),
            }
        except Exception as e:
            print(f"❌ Error, using fallback: {e}")
            return quick_result
    
    def _quick_classify(self, message):
        """Instant fallback classification using keywords"""
        msg = message.lower() if message else ""
        
        # Specific product keywords
        product_keywords = ["laptop", "phone", "shirt", "shoes", "bag", "watch", "headphone", 
                           "speaker", "tv", "monitor", "keyboard", "mouse", "chair", "desk", 
                           "book", "tablet", "nike", "adidas", "apple", "samsung", "dell", "hp"]
        if any(w in msg for w in product_keywords):
            return {"intent": "SEARCH_PRODUCTS", "keyword": message, "category_hint": ""}
        
        # Categories
        if any(w in msg for w in ["category", "list", "browse", "what do you have", "show all"]):
            return {"intent": "SHOW_CATEGORIES", "keyword": "", "category_hint": ""}
        
        # Featured
        if any(w in msg for w in ["featured", "popular", "trending", "top", "best selling"]):
            return {"intent": "SHOW_FEATURED", "keyword": "", "category_hint": ""}
        
        # Chitchat
        if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good evening", "how are you"]):
            return {"intent": "CHITCHAT", "keyword": "", "category_hint": ""}
        
        # Clarification
        if any(w in msg for w in ["gift", "suggest", "recommend", "help me", "what should"]):
            return {"intent": "ASK_CLARIFICATION", "keyword": "", "category_hint": ""}
        
        # Default to search
        return {"intent": "SEARCH_PRODUCTS", "keyword": message, "category_hint": ""}

    def classify_with_prompt(self, prompt):
        """For intent classifier - simplified for TinyLlama"""
        # Extract user message
        lines = prompt.split('\n')
        user_msg = ""
        for i, line in enumerate(lines):
            if "Latest user message:" in line and i+1 < len(lines):
                user_msg = lines[i+1].strip()
                break
        
        if user_msg:
            return self._quick_classify(user_msg)
        
        try:
            raw = self._post_generate(
                prompt=prompt, 
                format_json=True, 
                options={"temperature": 0.1, "num_predict": 50}
            )
            return json.loads(raw)
        except:
            return {"intent": "UNKNOWN"}

    def generate_conversation_json(self, user_message, chat_history, runtime_context):
        """Main conversation generator - optimized for TinyLlama"""
        
        # Quick response fallback
        quick_response = self._quick_response(user_message)
        
        # Try TinyLlama for better responses
        try:
            print("💬 Generating with TinyLlama...")
            
            # Simple, clear prompt for TinyLlama
            prompt = f"""You are a shopping assistant. Be helpful and concise.
Don't invent products. Keep response under 2 sentences.
End with a question.

User: {user_message[:150]}
Context: {runtime_context[:150] if runtime_context else "Shopping"}

Response JSON: {{"reply": "...", "product_ids": []}}"""
            
            raw = self._post_generate(
                prompt=prompt, 
                format_json=True, 
                options={"temperature": 0.4, "num_predict": 80}
            )
            print(f"📝 Raw: {raw}")
            parsed = json.loads(raw)
            print(f"✅ Parsed: {parsed}")
            
            product_ids = parsed.get("product_ids", [])
            if not isinstance(product_ids, list):
                product_ids = []
            product_ids = [int(pid) for pid in product_ids if str(pid).isdigit()][:5]
            
            return {
                "reply": (parsed.get("reply") or quick_response["reply"]).strip(),
                "product_ids": product_ids,
                "raw": parsed,
            }
        except Exception as e:
            print(f"❌ Error, using fallback: {e}")
            return quick_response
    
def _quick_response(self, message):
    """Instant fallback response with natural language"""
    msg = message.lower() if message else ""
    
    # Greetings
    if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good evening"]):
        return {"reply": "Hello! 👋 How can I help you shop today?", "product_ids": []}
    
    if any(w in msg for w in ["how are you", "how r u", "how's it going"]):
        return {"reply": "I'm doing great, thanks for asking! 😊 What products are you looking for?", "product_ids": []}
    
    if any(w in msg for w in ["what is your name", "who are you"]):
        return {"reply": "I'm Vendora AI, your personal shopping assistant! 🤖 What can I help you find?", "product_ids": []}
    
    if any(w in msg for w in ["what can you do", "help"]):
        return {"reply": "I can help you find products, show you categories, and recommend featured items! 🛍️ Just tell me what you're looking for.", "product_ids": []}
    
    if any(w in msg for w in ["thanks", "thank you"]):
        return {"reply": "You're welcome! 😊 Anything else I can help you with?", "product_ids": []}
    
    if any(w in msg for w in ["bye", "goodbye", "see you"]):
        return {"reply": "Goodbye! 👋 Have a great day and happy shopping!", "product_ids": []}
    
    # Products
    if any(w in msg for w in ["category", "list", "what do you have"]):
        return {"reply": "We have categories like Electronics, Clothing, Books, Home & Garden, and more. Which one interests you?", "product_ids": []}
    
    if any(w in msg for w in ["featured", "popular", "trending"]):
        return {"reply": "Check out our featured products on the homepage! They're our most popular items.", "product_ids": []}
    
    if any(w in msg for w in ["gift", "suggest", "recommend"]):
        return {"reply": "I'd love to help! 🎁 What's the occasion and who is it for?", "product_ids": []}
    
    if any(w in msg for w in ["laptop", "phone", "shirt", "shoes"]):
        return {"reply": f"Let me help you find the perfect {message}. What features are you looking for?", "product_ids": []}
    
    # Default
    return {"reply": f"I can help you find products related to '{message}'. Let me search for you! 🔍", "product_ids": []}


def generate_intelligent_response(self, user_message, context, history=None):
    """Generate intelligent response with full context"""
    
    prompt = f"""You are Vendora AI, an intelligent shopping assistant.

CONTEXT:
{context}

CHAT HISTORY:
{history if history else "No previous conversation"}

USER: {user_message}

Instructions:
1. Understand the user's real need
2. Use the provided context (database data)
3. Give a natural, human-like response
4. If products exist, mention them
5. If no products, suggest alternatives
6. Keep it conversational and helpful
7. End with a helpful question

Response should be JSON: {{"reply": "...", "product_ids": []}}"""

    try:
        raw = self._post_generate(prompt, format_json=True)
        return json.loads(raw)
    except:
        return {"reply": "I understand you're looking for something. Could you tell me more about what you need?", "product_ids": []}