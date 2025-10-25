from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # DRF-handled exceptions (400, 404, etc.)
        response.data = {
            "message": "Invalid Request",
            "errors": response.data
        }
    else:
        # Unhandled exceptions (500 errors)
        response = Response(
            {
                "message": "Server Error",
                "errors": {"detail": [str(exc)]}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response

