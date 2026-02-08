from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rental.models import Rental, Car, CarImage, Payment

#User Serializers

class CustomTokenObtailPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data



    #TODO 
    #User Dashboard
    #Forgot Password



# Car Serializers


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image']


class CarSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Car
        fields = [
            'id', 'name', 'brand', 'model_year', 'car_type',
            'transmission', 'fuel_type', 'seats', 'price_per_day',
            'is_available', 'created_at', 'images'
        ]
        #TODO use prefetch_related in view




class RentalSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
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
            "is_paid",
            "paid_at",
        ]
        read_only_fields = ["amount", "is_paid", "paid_at"]

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
        from django.utils import timezone
        
        rental = validated_data['rental']
        validated_data['amount'] = rental.total_price
        
        # Cash payments are unpaid initially (pay on pickup/delivery)
        if validated_data['payment_method'] == 'cash':
            validated_data['is_paid'] = False
            validated_data['paid_at'] = None  # Will be set when actually paid
        else:
            # PayPal or other methods - not implemented yet
            raise serializers.ValidationError("Only cash payment is supported currently")
        
        return super().create(validated_data)
