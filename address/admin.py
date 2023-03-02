from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'address',
        'latitude',
        'longitude',
        'last_handle_date',
    )