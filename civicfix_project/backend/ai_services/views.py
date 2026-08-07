from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import get_reply


class ChatbotAskSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)


class ChatbotAskView(APIView):
    """
    POST /api/chatbot/ask/  {message}  ->  {reply}
    Public (no login needed) so it can help on the login/register pages too.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatbotAskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = get_reply(serializer.validated_data["message"])
        return Response({"reply": reply})
