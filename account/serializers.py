from rest_framework import serializers 
from .models import User

class UserSerializer(serializers.ModelSerializer):
     password1 = serializers.CharField(write_only=True)
     password2 = serializers.CharField(write_only=True)

     class Meta:
          model = User
          fields = ['id', 'email', 'password1', 'password2']


     def validate(self,data):
          if data['password1'] != data['password2'] :
               raise serializers.ValidationError('Passwords don\'t match!')
          return data
     
     def create(self,validated_data):
          password = validated_data.pop('password1')
          validated_data.pop('password2',None)
          user = User.objects.create_user(password=password,**validated_data)
          return user
