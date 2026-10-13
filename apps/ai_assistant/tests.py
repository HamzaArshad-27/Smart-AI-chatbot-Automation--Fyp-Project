from django.test import SimpleTestCase

from apps.ai_assistant.chatbot import detect_intent, get_natural_response


class NaturalChatbotResponseTests(SimpleTestCase):
    def test_greeting_response_is_friendly(self):
        intent = detect_intent("hello")
        response = get_natural_response("hello", intent)["response"].lower()

        self.assertTrue(any(word in response for word in ["hello", "hi", "hey"]))
        self.assertIn("help", response)

    def test_chitchat_response_feels_human(self):
        intent = detect_intent("how are you")
        response = get_natural_response("how are you", intent)["response"].lower()

        self.assertIn("i", response)
        self.assertIn("help", response)

    def test_product_search_uses_natural_intro(self):
        intent = detect_intent("show me laptops")
        response = get_natural_response("show me laptops", intent)["response"].lower()

        self.assertIn("i found", response)
        self.assertNotIn("matching 'laptops'", response)
