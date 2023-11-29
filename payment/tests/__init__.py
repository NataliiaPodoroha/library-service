from payment.models import Payment


def sample_payment(borrowing, **params):
    defaults = {
        "status": "PENDING",
        "type": "PAYMENT",
        "borrowing": borrowing,
        "money_to_pay": "10.5",
        "session_url": "https://checkout.stripe.com/c/pay/",
        "session_id": f"test_id_{borrowing.id}",
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)
