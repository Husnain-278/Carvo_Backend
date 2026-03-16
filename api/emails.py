from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from rental.models import Rental
from django.contrib.auth import get_user_model


ACTIVATION_SALT = "account-activation"


def generate_activation_token(user_id: int) -> str:
    """Create a signed token for account activation."""
    return signing.dumps({"user_id": user_id}, salt=ACTIVATION_SALT)


def verify_activation_token(token: str) -> int:
    """Validate the activation token and return the user id."""
    data = signing.loads(
        token,
        max_age=int(getattr(settings, "ACTIVATION_TOKEN_MAX_AGE", 86400)),
        salt=ACTIVATION_SALT,
    )
    return data.get("user_id")


@shared_task
def send_activate_account_email(user_id: int):
    """Send activation link to the new user's email."""
    User = get_user_model()
    user = User.objects.get(id=user_id)
    token = generate_activation_token(user.id)
    activation_link = f"{settings.FRONTEND_URL}/activate?token={token}"

    subject = "Activate your Carvo account"
    message = f"""
Hi {user.username},

Welcome to Carvo! Please activate your account to start booking cars.

Activate your account:
{activation_link}

This link expires in 24 hours. If you didn't create an account, you can safely ignore this email.

Thanks,
The Carvo Team
"""
    send_mail(
        subject,
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


@shared_task
def send_rental_email(rental_id):
    """Send email when rental is confirmed (payment created)"""
    rental = Rental.objects.get(id = rental_id)
    payment = rental.payment
    
    subject = "✓ Rental Confirmed – Booking #" + str(rental.id)
    
    days = (rental.end_date - rental.start_date).days + 1
    
    # Determine payment status message
    if payment.payment_method == 'cash' and not payment.is_paid:
        payment_status = "💵 CASH PAYMENT - Pay on Pickup"
        payment_note = """⚠️ IMPORTANT: Cash Payment Required
→ Total amount due: ${}
→ Payment due: At vehicle pickup
→ Please bring exact amount or card as backup
""".format(rental.total_price)
    else:
        payment_status = "✅ PAYMENT CONFIRMED"
        payment_note = f"Payment of ${rental.total_price} has been processed successfully."
    
    message = f"""
Hi {rental.user.username},

Great news! Your rental has been confirmed! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CONFIRMED RENTAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Booking ID: #{rental.id}
Car: {rental.car.brand} {rental.car.name} ({rental.car.model_year})
Type: {rental.car.car_type}
Transmission: {rental.car.transmission}
Seats: {rental.car.seats}
Fuel Type: {rental.car.fuel_type}

📅 Rental Period: {days} day{"s" if days > 1 else ""}
   Pick-up: {rental.start_date.strftime('%B %d, %Y')}
   Drop-off: {rental.end_date.strftime('%B %d, %Y')}

💰 Total Amount: ${rental.total_price}
   (${rental.car.price_per_day}/day × {days} day{"s" if days > 1 else ""})

{payment_status}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{payment_note}

📝 PICKUP INFORMATION:

→ Please bring a valid driver's license and ID
→ Arrive 15 minutes early for vehicle inspection
→ Car will be fully fueled - please return it the same way
→ Any damages should be reported immediately

📍 Pick-up Location: @Carvo Garage Mars
⏰ Pick-up Time: 9:00 AM

Need help? Contact us immediately.

Enjoy your ride! 🚗💨

Best regards,
The Carvo Team
"""
    send_mail(
        subject,
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rental.user.email],
        fail_silently=False
    )


def send_rental_completed_email(rental):
    """Send email when rental is completed"""
    subject = "✓ Rental Completed – Thank You!"
    
    days = (rental.end_date - rental.start_date).days + 1
    
    message = f"""
Hi {rental.user.username},

Thank you for returning the {rental.car.brand} {rental.car.name}! 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RENTAL SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Booking ID: #{rental.id}
Car: {rental.car.brand} {rental.car.name} ({rental.car.model_year})

📅 Rental Period:
   Started: {rental.start_date.strftime('%B %d, %Y')}
   Ended: {rental.end_date.strftime('%B %d, %Y')}
   Duration: {days} day{"s" if days > 1 else ""}

💰 Total Paid: ${rental.total_price}

📊 Status: COMPLETED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We hope you enjoyed your experience with Carvo! 😊

⭐ Rate Your Experience:
Your feedback helps us improve our service. We'd love to hear about your experience!

🎁 Looking for your next adventure?
Browse our collection of premium vehicles for your next trip.

Thank you for choosing Carvo. We look forward to serving you again!

Best regards,
The Carvo Team
"""
    send_mail(
        subject,
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rental.user.email],
        fail_silently=False
    )


def send_rental_cancellation_email(rental):
    """Send email when rental is cancelled"""
    subject = "❌ Rental Cancelled – Booking #" + str(rental.id)
    
    days = (rental.end_date - rental.start_date).days + 1
    
    message = f"""
Hi {rental.user.username},

This email confirms that your rental booking has been cancelled.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ CANCELLED BOOKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Booking ID: #{rental.id}
Car: {rental.car.brand} {rental.car.name} ({rental.car.model_year})

📅 Original Rental Period:
   From: {rental.start_date.strftime('%B %d, %Y')}
   To: {rental.end_date.strftime('%B %d, %Y')}
   Duration: {days} day{"s" if days > 1 else ""}

💰 Amount: ${rental.total_price}

📊 Status: CANCELLED
🕒 Cancelled on: {rental.created_at.strftime('%B %d, %Y at %I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 REFUND INFORMATION:
If payment was processed, a full refund will be issued to your original payment method within 5-7 business days.

🚗 NEED ANOTHER CAR?
We have many other vehicles available! Browse our collection and find the perfect car for your needs.

If you have any questions about this cancellation, please don't hesitate to contact us.

We hope to serve you again soon!

Best regards,
The Carvo Team
"""
    send_mail(
        subject,
        message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[rental.user.email],
        fail_silently=False
    )