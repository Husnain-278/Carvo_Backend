from .serializers import *
from rental.models import *
from datetime import datetime
from django.db.models import Prefetch
from payments.services import create_checkout_session

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .emails import send_rental_email, send_activate_account_email, verify_activation_token
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.core import signing
from django.contrib.auth import get_user_model

# Create your views here.


class CarPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100


class RentalPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class CarListView(generics.ListAPIView):
    serializer_class = CarListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CarPagination

    def get_queryset(self):
      queryset = Car.objects.prefetch_related("images").filter(is_available=True)
      start_date = self.request.query_params.get("start_date") 
      end_date = self.request.query_params.get("end_date")
      if start_date and end_date:
          start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
          end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
          booked_car_ids = Rental.objects.filter(
              start_date__lte = end_date,
              end_date__gte = start_date,
              status__in = ["pending", "active"]
          ).values_list("car_id", flat=True)
          queryset = queryset.exclude(id__in= booked_car_ids)
          return queryset
      return queryset
    
class CarDetailView(generics.RetrieveAPIView):
    serializer_class = CarDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Car.objects.prefetch_related('images')
    lookup_field = 'slug'


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rental = serializer.validated_data["rental"]
        payment = getattr(rental, "payment", None)

        if payment is None:
           payment = serializer.save()
        
        #Stripe Payment
        if payment.payment_method == 'stripe':
            
            session = create_checkout_session(payment)
            
            payment.stripe_session_id = session.id
            payment.save(update_fields=["stripe_session_id"])
            return Response(
                {
                    "payment_id": payment.id,
                    "checkout_url": session.url,
                },
                status=status.HTTP_201_CREATED
            )
        
        #Cash Pyament
        payment.is_paid= True
        payment.save(update_fields=['is_paid'])
    
        payment.rental.status = 'active'
        payment.rental.save()
        send_rental_email.delay(payment.rental.id)
        return Response(
        self.get_serializer(payment).data,
        status=status.HTTP_201_CREATED
        )



class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        # Send activation email asynchronously
        send_activate_account_email.delay(user.id)
        return user


class ActivateAccountView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"detail": "Activation token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = verify_activation_token(token)
        except signing.SignatureExpired:
            return Response({"detail": "Activation link has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"detail": "Invalid activation token."}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({"detail": "Account is already activated."}, status=status.HTTP_200_OK)

        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({"detail": "Account activated successfully. You can now log in."}, status=status.HTTP_200_OK)



class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
    


class UserRentalView(generics.ListAPIView):
    serializer_class = UserRentalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        status_list = ['active', 'completed','cancelled']
        return Rental.objects.filter(
            user=self.request.user,
            status__in = status_list
        ).select_related('car')
    