from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()



class AIConversation(models.Model):
     user = models.ForeignKey(User,on_delete=models.CASCADE)
     created_at = models.DateTimeField(auto_now_add=True)

     def __str__(self):
          return f"user conversation: {self.user.email}"



class AIMessage(models.Model):
     MESSAGE_TYPE = [
          ('user','user message'),
          ('ai','ai response'),
     ]
     
     conversation = models.ForeignKey(AIConversation,on_delete=models.CASCADE,related_name='messages')
     message_type = models.CharField(max_length=10,choices=MESSAGE_TYPE,)
     content = models.TextField()
     timestamp = models.DateTimeField(auto_now_add=True)

