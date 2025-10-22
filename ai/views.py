from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import AIConversation, AIMessage
from .tasks import analyze_product_query_task
import json


class AIChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Accepts user queries like:
        {
            "message": "Show me blue sneakers under 1500"
        }
        Returns structured AI response + matching products
        """
        try:
            user_message = request.data.get("message", "").strip()
            if not user_message:
                return Response({"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

            conversation, _ = AIConversation.objects.get_or_create(user=request.user)

            user_msg = AIMessage.objects.create(
                conversation=conversation,
                message_type="user",
                content=user_message,
            )


            recent_messages = conversation.messages.filter(id__lt=user_msg.id).order_by("-timestamp")[:10]
            recent_messages_list = [
                {"message_type": m.message_type, "content": m.content}
                for m in recent_messages
            ]

            async_result = analyze_product_query_task.apply_async(
                args=[user_message, recent_messages_list]
            )
            ai_response = async_result.get(timeout=25)

            AIMessage.objects.create(
                conversation=conversation,
                message_type="ai",
                content=json.dumps(ai_response),
            )

            return Response({
                "conversation_id": conversation.id,
                "user_message": user_message,
                "ai_response": ai_response,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("AI Error:", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
