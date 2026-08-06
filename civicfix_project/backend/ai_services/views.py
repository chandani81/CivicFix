from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import get_reply
from .location_service import reverse_geocode


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


class ReverseGeocodeQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class ReverseGeocodeView(APIView):
    """Turn selected map coordinates into an address for the complaint form."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ReverseGeocodeQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        address = reverse_geocode(
            serializer.validated_data["latitude"],
            serializer.validated_data["longitude"],
        )
        return Response({"address": address})
