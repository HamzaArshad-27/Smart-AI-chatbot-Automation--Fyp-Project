# AI Assistant Setup

```bash
pip install requests
```

Optional LangChain integration:

```bash
pip install langchain langchain-community ollama
```

Run migrations:

```bash
python manage.py makemigrations ai_assistant
python manage.py migrate
```

Ensure Ollama is running:

```bash
ollama pull llama3.1:8b
ollama serve
```
