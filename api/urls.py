from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView
)
from .views import CustomTokenObtainPairView, ActivateAccountView

from . import views


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cars/', views.CarListView.as_view()),
    path('car-detail/<str:slug>/', views.CarDetailView.as_view(), name='list_cars'),
    path('rental/', views.RentalView.as_view()),
    path('payment/', views.PaymentView.as_view()),
    path('payment/execute/', views.PaymentExecuteView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('activate/', ActivateAccountView.as_view()),
    path('branch-list/',views.BranchListView.as_view()),
    path('user-profile/', views.UserProfileView.as_view()),
    path('user/rentals/', views.UserRentalView.as_view()),
    path('user/rental/', views.UserRentalView.as_view()),
]
