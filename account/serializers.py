from rest_framework import serializers 
from .models import User
class UserSerializer(serializers.ModelSerializer):
     password1 = serializers.CharField(write_only=True)
     password2 = serializers.CharField(write_only=True)
     roles = serializers.CharField(required=True)

     class Meta:
          model = User
          fields = ['id', 'email', 'password1', 'password2','roles']


     def validate(self,data):
          if data['password1'] != data['password2'] :
               raise serializers.ValidationError('Passwords don\'t match!')
          return data
     
     def create(self,validated_data):
          password = validated_data.pop('password1')
          validated_data.pop('password2',None)
          user = User.objects.create_user(password=password,**validated_data)
          return user

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def save(self, user):
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

