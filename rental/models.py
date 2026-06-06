from django.db import models
from accounts.models import CustomUser
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from uuid import uuid4
# Create your models here.

class Branch(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} - {self.city}"




class Car(models.Model):
    FUEL_CHOICES = (
        ("included", "Included"),
        ("excluded", "Ecluded")
    )

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    model_year = models.PositiveIntegerField()
    car_type = models.CharField(max_length=50)  
    transmission = models.CharField(max_length=20) 
    fuel_type = models.CharField(max_length=20) 
    seats = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True, null=True)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    slug = models.SlugField(blank=True, unique=True)
    fuel = models.CharField(max_length=10, choices=FUEL_CHOICES, default='included')
    current_branch = models.ForeignKey(
    Branch,
    on_delete=models.SET_NULL,
    null=True,
    related_name="cars"
)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.name} ({self.model_year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.name}-{self.brand}-{uuid4().hex[:4]}')
        super().save(*args, **kwargs)
           

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField('cars/', blank=True, null=True)




class Rental(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("expired","Expired")
    )
    FUEL_CHOICES = (
        ("included", "Included"),
        ("excluded", "Ecluded")
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="rentals")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="rentals")

    start_date = models.DateField()
    end_date = models.DateField()
    

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    fuel = models.CharField(max_length=10, choices=FUEL_CHOICES, default='included')
    pickup_branch= models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name="pickup_rentals")
    dropoff_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name="dropoff_rentals")
    

    created_at = models.DateTimeField(auto_now_add=True)
   






class Payment(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
       max_length=50,
       choices=[
             ("stripe", "Stripe"), 
             ("cash", "Cash"),
             ]
          )
    stripe_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)







# class Review(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="reviews")
#     rating = models.PositiveSmallIntegerField()
#     comment = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)