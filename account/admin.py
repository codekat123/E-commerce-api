from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'is_active', 'is_staff', 'roles', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'roles')
    search_fields = ('email',)
    ordering = ('-date_joined',)
