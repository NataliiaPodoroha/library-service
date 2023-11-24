import stripe
from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serializers import PaymentDetailSerializer, PaymentSerializer


class PaymentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Payment.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(borrowing__user_id=self.request.user.id)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentSerializer


def create_checkout_session(domain_url: str, borrowing_id: int, money_amount: int):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    borrowing = Borrowing.objects.get(pk=borrowing_id)
    book = Book.objects.get(pk=borrowing.book.id)
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success/",
            cancel_url=domain_url + "cancelled/",
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": money_amount,
                    "product_data": {
                        "name": book.title,
                        "description": "Book borrowing",
                    },
                },
                "quantity": 1,
            }],
        )
        return {"session_id": checkout_session["id"], "session_url": checkout_session["url"]}
    except Exception as e:
        return {"error": str(e)}
