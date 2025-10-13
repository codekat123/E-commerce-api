from rest_framework import serializers 
from .models import User

class UserSerializer(serializers.ModelSerializer):
     password1 = serializers.CharField(write_only=True)
     password2 = serializers.CharField(write_only=True)

     class Meta:
          model = User
          fields = ['id', 'email', 'password1', 'password2','roles']


     def validate(self, data):
         password1 = data.get('password1')
         password2 = data.get('password2')
     
         if password1 != password2:
             raise serializers.ValidationError("Passwords don't match!")
     
         if len(password1) < 8:
             raise serializers.ValidationError("Password must be at least 8 characters long.")
     
         return data
     
     def create(self,validated_data):
          password = validated_data.pop('password1')
          validated_data.pop('password2',None)
          user = User.objects.create_user(password=password,**validated_data)
          return user

