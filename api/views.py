from .serializers import *
from rental.models import *
from datetime import datetime
from django.db.models import Prefetch
import paypalrestsdk
from payments.paypal_config import *  # noqa: configures paypalrestsdk on import

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
        payment = serializer.save()

        if payment.payment_method == 'paypal':
            return self._handle_paypal(payment)

        # Cash: mark rental active immediately
        payment.rental.status = 'active'
        payment.rental.save()
        send_rental_email.delay(payment.rental.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_paypal(self, payment):
        from django.conf import settings
        paypal_payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"{settings.FRONTEND_URL}/payment/success",
                "cancel_url":  f"{settings.FRONTEND_URL}/payment/cancel",
            },
            "transactions": [{
                "amount": {
                    "total": str(payment.amount),
                    "currency": "USD",
                },
                "description": f"Car rental #{payment.rental.id}",
            }],
        })

        if paypal_payment.create():
            payment.paypal_payment_id = paypal_payment.id
            payment.save(update_fields=['paypal_payment_id'])
            approval_url = next(
                link.href for link in paypal_payment.links if link.rel == "approval_url"
            )
            return Response({
                "payment_id": payment.id,
                "paypal_payment_id": paypal_payment.id,
                "approval_url": approval_url,
            }, status=status.HTTP_201_CREATED)

        payment.delete()
        return Response({"detail": paypal_payment.error}, status=status.HTTP_400_BAD_REQUEST)


class PaymentExecuteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.utils import timezone
        paypal_payment_id = request.data.get('paypal_payment_id')
        payer_id = request.data.get('payer_id')

        if not paypal_payment_id or not payer_id:
            return Response(
                {"detail": "paypal_payment_id and payer_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.select_related('rental').get(
                paypal_payment_id=paypal_payment_id,
                rental__user=request.user,
            )
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.is_paid:
            return Response({"detail": "Payment already completed."}, status=status.HTTP_400_BAD_REQUEST)

        paypal_payment = paypalrestsdk.Payment.find(paypal_payment_id)
        if paypal_payment.execute({"payer_id": payer_id}):
            payment.is_paid = True
            payment.paid_at = timezone.now()
            payment.save(update_fields=['is_paid', 'paid_at'])
            payment.rental.status = 'active'
            payment.rental.save()
            send_rental_email.delay(payment.rental.id)
            return Response({"detail": "Payment completed successfully."}, status=status.HTTP_200_OK)

        return Response({"detail": paypal_payment.error}, status=status.HTTP_400_BAD_REQUEST)
    


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
    


class UserProfileView(generics.RetrieveAPIView):
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
    