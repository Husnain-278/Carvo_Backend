import stripe

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rental.models import Payment
from api.emails import send_rental_email

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )

    except ValueError:
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]
        stripe_session_id = session["id"]

        try:
            payment = Payment.objects.select_related(
                "rental"
            ).get(
                stripe_session_id=stripe_session_id
            )

        except Payment.DoesNotExist:
            return HttpResponse(status=404)

        # Prevent duplicate processing
        if payment.is_paid:
            return HttpResponse(status=200)

        payment.is_paid = True
        payment.paid_at = timezone.now()
        payment.save(
            update_fields=[
                "is_paid",
                "paid_at",
            ]
        )

        payment.rental.status = "active"
        payment.rental.save(
            update_fields=["status"]
        )

        send_rental_email.delay(
            payment.rental.id
        )

    return HttpResponse(status=200)