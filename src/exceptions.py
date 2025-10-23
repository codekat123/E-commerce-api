from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # If DRF already generated a response, modify it
    if response is not None:
        errors = response.data
        message = "Invalid Request"

        # Wrap everything under "message" and "errors"
        response.data = {
            "message": message,
            "errors": errors
        }

    else:
        # If it's not a DRF-handled exception, catch-all fallback
        response = Response(
            {"message": "Server Error", "errors": {"detail": ["Something went wrong."]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
