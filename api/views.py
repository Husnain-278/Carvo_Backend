from .serializers import *
from rental.models import *
import datetime

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .emails import send_rental_email
from django.core.cache import cache
from rest_framework.response import Response

# Create your views here.


class CarPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RentalPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtailPairSerializer


class CarView(generics.ListAPIView):
    serializer_class = CarSerializer
    queryset = Car.objects.prefetch_related('images').order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CarPagination 
    def list(self, request, *args, **kwargs):
        # Create a cache key based on page number
        page = request.query_params.get('page', 1)
        cache_key = f'cars_list_page_{page}'
        
        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            
            return Response(cached_data)
        
        # If not in cache, get from database
        response = super().list(request, *args, **kwargs)
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, response.data, 300)
        
        return response


class RentalView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RentalPagination
    serializer_class = RentalSerializer
    
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return Rental.objects.filter(user=user).select_related('user', 'car').prefetch_related('car__images')

    


class PaymentView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def perform_create(self, serializer):
        payment = serializer.save()
        payment.rental.status = 'active'
        payment.rental.save()
        send_rental_email.delay(payment.rental.id)
        return payment