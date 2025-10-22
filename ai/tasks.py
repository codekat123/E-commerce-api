from celery import shared_task
from django.conf import settings
from product.models import Product
from product.serializers import ProductSerializer
import google.generativeai as genai
import json
import re

SYSTEM_PROMPT = """
You are a helpful and friendly AI shopping assistant.
You help users find the right products by chatting with them.
When you reply, be conversational and helpful.
At the end of your reply, also include a JSON block with your analysis like this:

{
  "category": "",
  "keywords": [],
  "max_price": null,
  "min_price": null
}

The text before the JSON should be your human-readable message.
"""

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def analyze_product_query_task(self, user_message, conversation_history=None):
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        client = genai.GenerativeModel('gemini-2.5-flash')
        messages = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
        
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["message_type"] == "user" else "model"
                messages.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        messages.append({"role": "user", "parts": [{"text": user_message}]})
        
        completion = client.generate_content(messages)
        

        content = ""
        if completion.candidates:
            parts = completion.candidates[0].content.parts
            if parts:
                content = parts[0].text



        match = re.search(r'(\{.*\})', content, re.DOTALL)
        if match:
            json_part = match.group(1)
            human_reply = content.replace(json_part, "").strip()
            parsed = json.loads(json_part)
        else:
            human_reply = content.strip()
            parsed = {}.message.content
            parsed = json.loads(content)

        products = Product.objects.all()

        if parsed.get("category"):
            products = products.filter(category__name__icontains=parsed["category"])


        if parsed.get("keywords"):
            for kw in parsed["keywords"]:
                products = products.filter(name__icontains=kw)

        if parsed.get("max_price"):
            products = products.filter(price__lte=parsed["max_price"])

        if parsed.get("min_price"):
            products = products.filter(price__gte=parsed["min_price"])

        serialized = ProductSerializer(products[:10], many=True).data

        return {
            "query_analysis": parsed,
            "results": serialized,
            "human_reply":human_reply,
        }

    except Exception as exc:
        print("AI Task error:", exc)
        raise exc
