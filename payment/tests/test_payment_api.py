from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from borrowing.tests import create_user, sample_book, sample_borrowing
from payment.models import Payment
from payment.serializers import PaymentSerializer
from payment.tests import sample_payment

PAYMENTS_URL = reverse("payment:payment-list")
BORROWING_URL = reverse("borrowing:borrowing-list")


def success_url(payment_id):
    return reverse("payment:payment-success", args=[payment_id])


class UnauthenticatedPaymentsApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPaymentsApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="first@test.com",
            password="firstpass",
            is_staff=False,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_only_users_payments(self):
        book = sample_book()
        user_borrowing = sample_borrowing(book, self.user)

        second_user = create_user(
            email="second@test.com",
            password="secondpass",
            is_staff=False,
        )
        second_user_borrowing = sample_borrowing(book, second_user)

        payment_first_user = sample_payment(user_borrowing)
        payment_second_user = sample_payment(second_user_borrowing)

        res = self.client.get(PAYMENTS_URL)

        serializer1 = PaymentSerializer(payment_first_user)
        serializer2 = PaymentSerializer(payment_second_user)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_create_payment_for_borrowing(self):
        book = sample_book()

        payload = {"expected_return_date": "2023-12-12", "book": book.id}

        res = self.client.post(BORROWING_URL, payload)

        borrowing = res.data.serializer.instance

        payment = Payment.objects.first()

        self.assertEqual(payment.borrowing, borrowing)
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(payment.type, "PAYMENT")
        self.assertIsNotNone(payment.session_url)
        self.assertIsNotNone(payment.session_id)


class SuccessEndpointApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="test@test.com", password="testpass")
        self.client.force_authenticate(self.user)

    @patch("stripe.checkout.Session.retrieve")
    def test_success_endpoint(self, mock_session_retrieve):
        book = sample_book()
        borrowing = sample_borrowing(book, self.user)
        payment = sample_payment(borrowing)

        mock_session_retrieve.return_value = {
            "id": payment.session_id,
            "payment_status": "paid",
        }

        response = self.client.get(success_url(payment.id))

        updated_payment = Payment.objects.get(pk=payment.pk)
        self.assertEqual(updated_payment.status, "PAID")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PaymentSerializer(updated_payment)
        self.assertEqual(response.data, serializer.data)
