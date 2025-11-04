from rest_framework import serializers 
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    roles = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password1', 'password2', 'roles', 'terms_accepted']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password2': ["Passwords don't match!"]})
        
        if not data.get('terms_accepted', False):
            raise serializers.ValidationError({'terms_accepted': ["You must accept our terms to sign up."]})
        
        return data

    def create(self, validated_data):
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)
        user = User.objects.create_user(password=password, **validated_data)
        return user

class RequestResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
