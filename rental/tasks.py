from .models import Rental
from celery import shared_task

@shared_task
def expire_unpaid_rental(rental_id):
    try:
        rental = Rental.objects.get(id = rental_id)
        if rental.status == 'pending':
            rental.status = 'expired'
            rental.save()
    except Rental.DoesNotExist:
        pass