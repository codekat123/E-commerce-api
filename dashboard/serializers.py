from rest_framework import serializers


class DateSerializer(serializers.Serializer):
     date_from = serializers.DateField()
     date_to = serializers.DateField()