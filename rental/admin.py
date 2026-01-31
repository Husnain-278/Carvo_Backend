from django.contrib import admin
from .models import Car, CarImage, Rental, Payment


# Inline for Car Images
class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1
    fields = ('image',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model_year', 'car_type', 'price_per_day', 'is_available')
    list_filter = ('brand', 'car_type', 'transmission', 'fuel_type', 'is_available')
    search_fields = ('name', 'brand')
    list_editable = ('is_available',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'model_year')
        }),
        ('Specifications', {
            'fields': ('car_type', 'transmission', 'fuel_type', 'seats')
        }),
        ('Pricing & Availability', {
            'fields': ('price_per_day', 'is_available')
        }),
    )
    
    inlines = [CarImageInline]


# Enable autocomplete for Car
CarAdmin.search_fields = ['name', 'brand']


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'start_date', 'end_date', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__username', 'car__name', 'car__brand')
    readonly_fields = ('created_at',)
    list_select_related = ('user', 'car')
    autocomplete_fields = ('user', 'car')
    
    fieldsets = (
        ('Rental Details', {
            'fields': ('user', 'car', 'start_date', 'end_date')
        }),
        ('Payment & Status', {
            'fields': ('total_price', 'status')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('rental', 'amount', 'payment_method', 'is_paid', 'paid_at')
    list_filter = ('is_paid', 'payment_method', 'paid_at')
    search_fields = ('rental__user__username', 'rental__car__name')
    readonly_fields = ('paid_at',)
    list_select_related = ('rental', 'rental__user', 'rental__car')
    autocomplete_fields = ('rental',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('rental', 'amount', 'payment_method')
        }),
        ('Payment Status', {
            'fields': ('is_paid', 'paid_at')
        }),
    )
