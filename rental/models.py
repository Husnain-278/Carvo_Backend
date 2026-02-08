from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
# Create your models here.



class Car(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    model_year = models.PositiveIntegerField()
    car_type = models.CharField(max_length=50)  
    transmission = models.CharField(max_length=20) 
    fuel_type = models.CharField(max_length=20) 
    seats = models.PositiveSmallIntegerField()

    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.name} ({self.model_year})"




class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField('cars/', blank=True, null=True)




class Rental(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rentals")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="rentals")

    start_date = models.DateField()
    end_date = models.DateField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
   






class Payment(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
       max_length=50,
       choices=[
             ("paypal", "PayPal"),
             ("cash", "Cash"),
             ]
          )
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)







# class Review(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="reviews")
#     rating = models.PositiveSmallIntegerField()
#     comment = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)