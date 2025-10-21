# from asgiref.sync import sync_to_async
# import os
# import django

# # Set the DJANGO_SETTINGS_MODULE environment variable
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

# # Initialize Django
# django.setup()

# from typing import Final
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from order.models import Order  # Import Order model after django.setup()

# BOT_TOKEN = os.getenv('BOT_TOKEN')
# BOT_USERNAME: Final = '@codekat_bot'


# @sync_to_async
# def get_order_by_id(order_id):
#     """
#     Synchronously retrieves the order by its ID and returns a string with its details.
#     This function is wrapped with sync_to_async to allow use in an async context.
#     """
#     try:
#         # Search for the order in the database
#         order = Order.objects.get(order_id=order_id)
#         return (
#             f"Order ID: {order.order_id}\n"
#             f"Status: {order.get_status()}\n"  # Use get_status_display() for a readable status
#             f"Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
#             f"Product: {order.get_products()}\n"
#             f"Address: {order.address}"
#         )
#     except Order.DoesNotExist:
#         return f"Order with ID {order_id} does not exist."


# async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """
#     Handles the /start command.
#     """
#     username = update.message.from_user.username
#     await update.message.reply_text(
#         f"Hello, {username}! I am a Management Order Bot.\nPlease enter your Order ID to check its status."
#     )


# async def handle_order_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """
#     Handles messages sent to the bot. Expects an order ID as the input.
#     """
#     text = update.message.text.strip()
#     if not text:
#         return  

#     order_id = text
#     response = await get_order_by_id(order_id) 
#     await update.message.reply_text(response)


# if __name__ == '__main__':
#     print('Starting bot...')
#     app = Application.builder().token(BOT_TOKEN).build()

#     # Add handlers
#     app.add_handler(CommandHandler('start', start_command))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_query))

#     print('Polling...')
#     app.run_polling(poll_interval=3)