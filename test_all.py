import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendora.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.ai_assistant.chatbot import process_chat_message
import time

User = get_user_model()

def run_tests():
    print("="*70)
    print("🧪 CHATBOT COMPLETE TEST SUITE")
    print("="*70)
    
    user = User.objects.first()
    if not user:
        print("❌ No user found!")
        return
    
    test_categories = {
        "🟢 Greetings & Chitchat": [
            "hello", "hi", "how are you", "what is your name", 
            "what can you do", "thank you", "bye"
        ],
        "🟡 Urdu/Hindi": [
            "kese ho", "salam", "mujhe laptop chahiye", 
            "categories dikhao", "kitne products hain"
        ],
        "🔵 General Info": [
            "how many products do you have", 
            "what are your categories",
            "tell me about your store"
        ],
        "🟣 Product Search": [
            "show me laptops", "i need a phone", "shoes", 
            "watches", "bags", "clothing"
        ],
        "🟠 Specific Products": [
            "gaming laptops", "cars", "electronics", 
            "jewelry", "sports shoes", "winter jackets"
        ],
        "🔴 Natural Language": [
            "i'm looking for something special",
            "what's the best product",
            "show me something popular",
            "what do you have in electronics",
            "suggest a good laptop"
        ]
    }
    
    all_results = []
    
    for category, queries in test_categories.items():
        print(f"\n{'='*70}")
        print(f"📂 {category}")
        print('='*70)
        
        for query in queries:
            print(f"\n👤 User: {query}")
            
            start = time.time()
            try:
                result, state = process_chat_message(user, query, {})
                elapsed = time.time() - start
                
                response = result.get('response', '').replace('\n', ' ')
                suggestions = len(result.get('suggestions', []))
                
                print(f"🤖 AI: {response[:200]}")
                print(f"⏱️ {elapsed:.2f}s | 📦 {suggestions} products")
                
                all_results.append({
                    "query": query,
                    "category": category,
                    "response": response[:200],
                    "suggestions": suggestions,
                    "time": elapsed
                })
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Total tests: {len(all_results)}")
    print(f"Average time: {sum(r['time'] for r in all_results) / len(all_results):.2f}s")
    print(f"Products found: {sum(r['suggestions'] for r in all_results)}")
    
    return all_results

if __name__ == "__main__":
    run_tests()