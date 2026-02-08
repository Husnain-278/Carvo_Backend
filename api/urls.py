from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import CustomTokenObtainPairView
from . import views


urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cars/', views.CarView.as_view(), name='list_cars'),
    path('rental/', views.RentalView.as_view()),
    path('payment/', views.PaymentView.as_view()),
]
