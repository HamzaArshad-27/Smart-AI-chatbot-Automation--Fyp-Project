# AI Assistant (Vendora) — Technical Report

## Overview
This document describes the AI Assistant implemented in `apps/ai_assistant`. It explains how the chatbot works, the key implementation files and components, the public API/URLs, and detailed recommendations to improve naturalness, authenticity, and accuracy.

## High-level architecture
- Frontend (JS UI) sends user messages to the Django API endpoints in `apps.ai_assistant.views`.
- `chatbot.process_chat_message()` is the main orchestration function: it normalizes input, performs intent detection, chooses between a data-driven response (JSON trainer/knowledge) or a natural LLM response (Ollama), updates user preferences, caches results, persists chat history, and returns structured payloads (response, suggestions, quick replies).
- Data components:
  - `JSONTrainer` (`json_trainer.py`) — in-memory index and scoring for product search, trending, featured, and stats.
  - `JSONKnowledgeBase` (`json_knowledge_base.py`) — raw JSON data loader and query helpers.
  - `WebsiteDataLoader` (in `data_loader.py`) and cached helpers that load real DB/product data for the AIAgent.
- LLM integration: `services.ollama_client.OllamaClient` is used in `chatbot.py` and `ai_agent.py` to generate natural conversational replies and to run analysis/classification prompts.
- Advanced agent: `AIAgent` (`ai_agent.py`) builds a richer context (website stats, categories, product lists) and uses Ollama for a retrieval-augmented style response when deeper database access is needed.

## How the chatbot works (step-by-step)
1. Frontend sends POST `/ai_assistant/chat/` with JSON `{ "message": "..." }`.
2. `views.chat_api` validates the user and payload, reads session state, and calls `process_chat_message(user, message, graph_state)`.
3. `process_chat_message`:
   - Normalizes the message and checks the cache for a recent identical query.
   - Loads recent messages from `ChatHistory` for context (limited by `RECENT_HISTORY_LIMIT`).
   - Calls `detect_intent(message)` to classify intent (chitchat, categories, stats, trending, featured, help, product_search).
   - If `chitchat`, it calls `get_ollama_natural_response()` which attempts a fast local fallback set of replies then calls Ollama via `OllamaClient.generate_conversation_json()` (with a runtime_context instruction). There are multiple levels of fallback to avoid timeouts.
   - Otherwise, it uses `get_data_response()` (which consults the `trainer` JSON index) to prepare data-driven responses (search results, categories, trending, stats, featured, help text).
   - Tracks interest via `update_user_preferences()` and stores `ChatHistory` entries.
   - Computes quick-reply suggestions (`get_quick_replies`) and personalized recommendations (`get_personalized_recommendations`) when applicable.
   - Caches the reply, returns JSON payload and updates session `ai_graph_state`.

## Key implementation files
- [apps/ai_assistant/chatbot.py](apps/ai_assistant/chatbot.py#L1) — main conversation orchestration, intent detection, fallback logic, caching, suggestions.
- [apps/ai_assistant/json_trainer.py](apps/ai_assistant/json_trainer.py#L1) — search, ranking, trending/featured selection, basic indexing logic.
- [apps/ai_assistant/json_knowledge_base.py](apps/ai_assistant/json_knowledge_base.py#L1) — JSON loader and simple query helpers.
- [apps/ai_assistant/ai_agent.py](apps/ai_assistant/ai_agent.py#L1) — advanced agent that builds a rich prompt/context and uses Ollama to generate responses with DB grounding.
- [apps/ai_assistant/intent_classifier.py](apps/ai_assistant/intent_classifier.py#L1) — quick keyword-based classifier with Ollama fallback for ambiguous cases.
- [apps/ai_assistant/views.py](apps/ai_assistant/views.py#L1) — API endpoints the frontend calls.
- [apps/ai_assistant/urls.py](apps/ai_assistant/urls.py#L1) — routes: `/chat/`, `/interest/`, `/data/refresh/`, `/data/stats/`.
- [apps/ai_assistant/services/ollama_client.py](apps/ai_assistant/services/ollama_client.py#L1) — (LLM client wrapper) used throughout for classification and generation.

## API endpoints (routes)
- POST `/ai_assistant/chat/` — main chat API (`views.chat_api`). Request: `{message}`. Response: `{ response, suggestions, quick_replies }`.
- POST `/ai_assistant/interest/` — track user interest (view/like/dislike) for personalization (`views.track_interest_api`). Request: `{ product_id, interest_type }`.
- POST `/ai_assistant/data/refresh/` — admin-only endpoint to refresh AI data (`views.refresh_data_api`).
- GET `/ai_assistant/data/stats/` — returns `stats`, `categories`, and `trending` for UI widgets.

## Current strengths and design decisions
- Hybrid approach: combines a fast, deterministic JSON index (`trainer`) for product-centric queries with an LLM (Ollama) for chitchat and complex analysis.
- Local fallbacks: avoids LLM calls for common greetings and uses cached responses to reduce latency.
- Personalization hooks: `update_user_preferences`, `UserProductInterest`, and `AIResponseGenerator` tracking allow the assistant to recommend personalized items.
- Safe admin controls: cached website stats, and an admin refresh endpoint to rebuild AI datasets.

## Detailed recommendations to improve naturalness, authenticity, and accuracy
Below are concrete, prioritized improvements with implementation guidance.

1) Retrieval-Augmented Generation (RAG) with embeddings
   - Build an embedding index for product descriptions, titles, FAQs, and knowledge articles using `sentence-transformers` or OpenAI/other embeddings.
   - Store vector index in FAISS (local) or Milvus/Weaviate (service) for scalable similarity search.
   - For each user query, retrieve top-K grounded documents and include them as context to the LLM prompt. This reduces hallucination and increases accuracy.
   - Include source attribution in responses (e.g., “According to the product listing: … — [product link]”).

2) Better Context & Long-Term Memory
   - Implement a session summary or memory store: compress recent conversation into a short summary with embeddings and pass to LLM as persistent context.
   - Maintain user profile vectors (preferences, liked brands, price range) to personalize results without re-querying DB each time.
   - Use conversation state machine (dialog manager) for slot-filling flows (e.g., narrowing search by price, brand, size).

3) Intent & Entity Extraction (NLU)
   - Replace or augment keyword intent detection with a small fine-tuned classifier (transformer) or a lightweight intent+entity pipeline using spaCy or a BERT-based classifier.
   - Extract structured entities: product_type, brand, price_range, color, size — then map them into structured DB queries.
   - Add a confidence threshold; for low-confidence cases, ask concise clarification questions rather than guessing.

4) Grounding & Canonical Product Response
   - When recommending, return canonical product IDs, URLs, prices and images (structured suggestions) along with natural text.
   - Use templated response composer for product lists to keep tone consistent and reduce hallucinations.

5) Response Quality Controls
   - Temperature/creativity: use lower temperature for factual responses, higher for casual chitchat.
   - Add a lightweight verifier: after LLM generates a factual claim about product specs, re-check against product DB and correct contradictions before sending.
   - Add guardrails for policy/safety and profanity filters.

6) Faster & More Reliable LLM Interaction
   - Implement async/streaming responses where the server streams partial text to the frontend for perceived responsiveness.
   - Add circuit-breaker and fallback: if Ollama fails or times out, degrade gracefully to `trainer` results or cached replies.

7) Improved Personalization & Recommendations
   - Combine content-based embeddings (product vectors) with collaborative filtering (user-item interactions) for personalized ranking.
   - Use signals from `UserProductInterest` (view/like/dislike) to update user embeddings incrementally.

8) Evaluation, Metrics & A/B testing
   - Log structured conversation events and outcomes (clicked suggestion, converted to purchase, user feedback) and compute metrics: CTR of suggestions, satisfaction rating, conversion lift.
   - Run A/B tests for different prompt templates, reply formats, and recommendation ranking strategies.

9) Data Pipeline & Continuous Improvement
   - Automate product export and indexing: create scheduled jobs to refresh JSON/embeddings and rebuild indices.
   - Add synthetic data augmentation and paraphrase augmentation for intent/entity training.
   - Provide developer tools for sampling conversations and replaying with different models/prompt templates.

10) UX and Naturalness
   - Define a concise persona prompt (tone, role, constraints) used consistently for all Ollama generations to keep voice stable and friendly.
   - Use quick-reply suggestions adaptively based on context and avoid repeating suggestions too often.
   - Use microcopy and follow-ups (e.g., “Would you like me to filter by price or brand?”) to make interactions feel collaborative.

## Suggested short-term implementation plan
1. Add embeddings-based similarity search for product grounding (use `sentence-transformers` + FAISS).
2. Implement retrieval step in `AIAgent._build_context` and in `chatbot.get_ollama_natural_response` so LLM responses are grounded by product docs.
3. Add entity extractor (spaCy rule-based patterns) to `detect_intent` to capture brand/price/size for immediate improvements.
4. Add a verifier step after LLM reply to check factual product attributes against DB before returning to user.

## Useful references & next steps
- To add embeddings: see `sentence-transformers`, `faiss`.
- For RAG architecture: implement retriever → prompt builder → LLM generator → verifier pipeline.
- If you'd like, I can: implement embeddings+FAISS bootstrap, add an entity extractor, or create an A/B test harness for reply templates.

---
Report created from the current codebase in `apps/ai_assistant`. If you want, I can commit this file and implement one of the enhancements above next.
