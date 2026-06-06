import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(payment):
  session = stripe.checkout.Session.create(
    payment_method_types = ['card' ],
    line_items=[
        {
            "price_data":{
                "currency":"usd",
                "product_data":{
                    "name": f"Car Rental #{payment.rental.id}",
                },
                "unit_amount": int(payment.amount * 100),
            },
            "quantity": 1,
        }
    ],
    mode="payment",
    success_url=f"{settings.FRONTEND_URL}/payment/success",
    cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
    metadata={
            "payment_id": payment.id,
            "rental_id": payment.rental.id,
        }
   )
  return session