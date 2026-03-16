from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rental.models import Rental, Car, CarImage, Payment
from django.contrib.auth import get_user_model
import re
#User Serializers

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_password(self, value):
        """
        Validate password strength:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
     
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")
        
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise AuthenticationFailed("Account is not activated. Please check your email for the activation link.")
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data



    #TODO 
    #User Dashboard
    #Forgot Password



# Car Serializers


class CarImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = CarImage
        fields = ['id', 'image']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

class CarListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id',
            'name',
            'slug',
            'brand',
            'model_year',
            'car_type',
            'seats',
            'price_per_day',
            'is_available',
            'image'
        ]

    def get_image(self, obj):
        images = obj.images.all()   # uses prefetched data
        if images:
            return images[0].image.url
        return None
        
class CarDetailSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Car
        fields = [
            'id', 'name', 'brand', 'model_year', 'car_type',
            'transmission', 'fuel_type', 'seats', 'price_per_day',
            'is_available', 'created_at', 'description', 'images'
        ]
        #TODO use prefetch_related in view




class RentalSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    car_id = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(),
        source='car',
        write_only=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Rental
        fields = [
             'id', 'username', 'car', 'car_id',
             'start_date', 'end_date', 'total_price',
             'status', 'created_at'
                ]
        read_only_fields = ['total_price', 'status', 'created_at']
        
    def validate(self, data):
        # Validate date range
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        
        car = data['car']
        
        # Check if car is available
        if not car.is_available:
            raise serializers.ValidationError("This car is not available for rental")
        
        # Check for overlapping rentals
        overlapping = Rental.objects.filter(
            car=car,
            status__in=['pending', 'active'],
            start_date__lte=data['end_date'],
            end_date__gte=data['start_date']
        )
        
        if overlapping.exists():
            raise serializers.ValidationError("This car is already booked for the selected dates")
        
        return data
    
    def create(self, validated_data):
        car = validated_data['car']
        days = (validated_data['end_date'] - validated_data['start_date']).days + 1
        validated_data['total_price'] = car.price_per_day * days
        return super().create(validated_data)



class PaymentSerializer(serializers.ModelSerializer):
    rental_id = serializers.PrimaryKeyRelatedField(
        queryset=Rental.objects.all(),
        source="rental",
        write_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "rental_id",
            "amount",
            "payment_method",
            "paypal_payment_id",
            "is_paid",
            "paid_at",
        ]
        read_only_fields = ["amount", "paypal_payment_id", "is_paid", "paid_at"]

    def validate(self, data):
        rental = data["rental"]

        # Ensure user owns the rental
        if rental.user != self.context["request"].user:
            raise serializers.ValidationError("Not your rental")

        # Prevent duplicate payment
        if hasattr(rental, "payment"):
            raise serializers.ValidationError("Payment already exists")

        return data
    
    def create(self, validated_data):
        rental = validated_data['rental']
        validated_data['amount'] = rental.total_price
        validated_data['is_paid'] = False
        validated_data['paid_at'] = None
        return super().create(validated_data)
