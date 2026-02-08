from django.contrib import admin
from .models import Car, CarImage, Rental, Payment
from api.emails import  send_rental_cancellation_email, send_rental_completed_email


# Inline for Car Images
class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1
    fields = ('image',)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model_year', 'car_type', 'price_per_day', 'is_available')
    
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
    
    def save_model(self, request, obj, form, change):
        if change:
            old_status = Rental.objects.get(pk = obj.pk).status
        else:
            old_status = None
        super().save_model(request, obj, form, change)
        if change and old_status != obj.status:
            if obj.status == 'completed':
                send_rental_completed_email(obj)
            elif obj.status == 'cancelled':
                send_rental_cancellation_email(obj)
            else:
                pass



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('rental', 'amount', 'payment_method', 'is_paid', 'paid_at')
    readonly_fields = ('paid_at',)
    list_select_related = ('rental', 'rental__user', 'rental__car')
   
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('rental', 'amount', 'payment_method')
        }),
        ('Payment Status', {
            'fields': ('is_paid', 'paid_at')
        }),
    )
