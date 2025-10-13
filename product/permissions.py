from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsMerchantOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Anyone can read (GET), but only authenticated merchants can write (POST, PUT, DELETE)
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and hasattr(request.user, 'merchant_profile')

    def has_object_permission(self, request, view, obj):
        # Merchants can only modify their own products
        if request.method in SAFE_METHODS:
            return True
        return obj.merchant.user == request.user
    

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff