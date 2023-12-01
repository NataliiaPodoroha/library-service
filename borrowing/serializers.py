import stripe
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from book.serializers import BookSerializer
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serializers import PaymentSerializer
from payment.views import create_checkout_session
from user.serializers import UserSerializer


class BorrowingListSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    payments = serializers.HyperlinkedRelatedField(
        view_name="payment:payment-detail",
        many=True,
        read_only=True
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "user_email",
            "payments",
        )
        read_only_fields = ("actual_return_date",)


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "actual_return_date",
            "expected_return_date",
            "book",
            "user",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("expected_return_date", "book")

    def validate(self, data):
        book = data["book"]
        if book.inventory == 0:
            raise serializers.ValidationError("The book is out of stock.")
        return data

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data.get("book")
            borrowing = Borrowing.objects.create(**validated_data)
            book.inventory -= 1
            book.save()
            request = self.context["request"]
            create_payment(request, borrowing, borrowing.price, "PAYMENT")
            return borrowing


class BorrowingReturnSerializer(serializers.ModelSerializer):
    book = BookSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = (
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )

    def validate(self, data):
        if self.instance.actual_return_date:
            raise serializers.ValidationError(
                "This borrowing has already been returned."
            )
        return data

    def save(self, **kwargs):
        with transaction.atomic():
            self.instance.actual_return_date = timezone.now().date()
            book = self.instance.book
            request = self.context["request"]
            book.inventory += 1
            book.save()

            if self.instance.actual_return_date > self.instance.expected_return_date:
                create_payment(request, self.instance, self.instance.overdue, "FINE")

            return super().save(**kwargs)


def create_payment(request, borrowing: Borrowing, money_amount: int, payment_type: str):
    payment = Payment.objects.create(
        status="PENDING",
        type=payment_type,
        borrowing=borrowing,
        money_to_pay=money_amount,
    )

    base_url = request.build_absolute_uri(
        reverse("payment:payment-detail", kwargs={"pk": payment.id})
    )

    money_amount = int(money_amount * 100)

    session_data = create_checkout_session(base_url, borrowing.id, money_amount)

    if session_data.get("error", None):
        raise stripe.error.APIError

    payment.session_url = session_data["session_url"]
    payment.session_id = session_data["session_id"]
    payment.save()
