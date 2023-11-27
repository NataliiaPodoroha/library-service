import stripe
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from borrowing.models import Borrowing
from borrowing.permissions import IsAdminOrIfAuthenticatedReadOrCreateOnly
from borrowing.serializers import (
    BorrowingCreateSerializer,
    BorrowingDetailSerializer,
    BorrowingListSerializer, BorrowingReturnSerializer,
)
from payment.models import Payment
from payment.views import create_checkout_session


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user")
    permission_classes = [IsAdminOrIfAuthenticatedReadOrCreateOnly]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if user.is_staff:
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        else:
            queryset = queryset.filter(user=user)

        if is_active:
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "return_book":
            return BorrowingReturnSerializer
        return BorrowingListSerializer

    @action(methods=["POST"], detail=True, url_path="return")
    def return_book(self, request, pk=None):
        borrowing = get_object_or_404(Borrowing, pk=pk)

        if borrowing.actual_return_date:
            return Response(
                {"detail": "The book has already been returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (payment_obj := borrowing.payments.filter(status="PENDING")).exists():
            return HttpResponseRedirect(payment_obj.first().session_url)

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            book = borrowing.book
            book.inventory += 1

            book.save()
            borrowing.save()
        if borrowing.actual_return_date > borrowing.expected_return_date:
            self.create_payment(self.request, borrowing, borrowing.overdue, "FINE")

        return Response(
            {"message": "Borrowing returned successfully."}, status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        with transaction.atomic():
            borrowing = serializer.save(user=self.request.user)

            book = borrowing.book
            book.inventory -= 1
            book.save()

            self.create_payment(self.request, borrowing, borrowing.price, "PAYMENT")

    @staticmethod
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
