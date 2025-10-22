from celery import shared_task
from django.conf import settings
from product.models import Product
from product.serializers import ProductSerializer
import openai
import json

SYSTEM_PROMPT = """
You are an AI assistant for an e-commerce platform.
Analyze the user's query and return structured JSON like:
{
  "category": "",
  "keywords": [],
  "max_price": null,
  "min_price": null,
}
"""

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def analyze_product_query_task(self, user_message, conversation_history=None):
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["message_type"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        # Run model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        content = completion.choices[0].message.content
        parsed = json.loads(content)

        # Query database dynamically
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
        }

    except Exception as exc:
        print("AI Task error:", exc)
        raise exc
