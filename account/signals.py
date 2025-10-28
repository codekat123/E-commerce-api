from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from user_profile.models import CustomerProfile, MerchantProfile
from .tasks import send_email_task
from .utils import generate_otp,store_otp


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.roles == "Merchant":
            MerchantProfile.objects.create(user=instance)
        else:
            CustomerProfile.objects.create(user=instance)
        
@receiver(post_save,sender=User)
def send_otp(sender,instance,created,**kwargs):
    if created:
        subject = f"please active your account"
        otp = generate_otp()
        store_otp(instance.email,otp)
        html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
          <h2 style="color: #007BFF;">Welcome to <strong>ShopAI</strong> 👋</h2>
          <p>Here’s your One-Time Password (OTP) to verify your email and activate your account:</p>

          <div style="font-size: 24px; font-weight: bold; background: #f0f4ff; color: #007BFF;
                      padding: 10px 0; text-align: center; border-radius: 6px; letter-spacing: 4px;">
            {otp}
          </div>

          <p style="margin-top: 20px;">⚠️ This OTP will expire in <strong>5 minutes</strong>.</p>
          <p>If you didn’t request this, please ignore this email.</p>

          <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
          <p style="font-size: 12px; color: #777;">Thanks for choosing ShopAI 💙</p>
        </div>
      </body>
    </html>
    """
        send_email_task(
    subject=subject,
    html_content=html_content,
    recipient_list=[instance.email]  # 👈 wrap in brackets
)

        
