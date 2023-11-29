from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from book.models import Book
from borrowing.serializers import BorrowingListSerializer
from borrowing.tests import create_user, sample_book, sample_borrowing

BORROWING_URL = reverse("borrowing:borrowing-list")
PAYMENTS_URL = reverse("payment:payment-list")


def return_url(borrowing_id):
    return reverse("borrowing:borrowing-return-book", args=[borrowing_id])


class UnauthenticatedBorrowingsApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingsApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="first@test.com",
            password="firstpass",
            is_staff=False,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_only_users_borrowings(self):
        book = sample_book()
        user_borrowing = sample_borrowing(book, self.user)

        second_user = create_user(
            email="second@test.com",
            password="secondpass",
            is_staff=False,
        )
        second_user_borrowing = sample_borrowing(book, second_user)
        res = self.client.get(BORROWING_URL)

        serializer1 = BorrowingListSerializer(user_borrowing)
        serializer2 = BorrowingListSerializer(second_user_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtering_is_active(self):
        book = sample_book()
        activ_borrowing = sample_borrowing(book, self.user)
        non_active_borrowing = sample_borrowing(
            book, self.user, actual_return_date="2025-10-12"
        )

        res = self.client.get(BORROWING_URL, {"is_active": True})

        serializer1 = BorrowingListSerializer(activ_borrowing)
        serializer2 = BorrowingListSerializer(non_active_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)


class AdminBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="admin@admin.com",
            password="adminpass",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_all_borrowings(self):
        book = sample_book()
        user_borrowing = sample_borrowing(book, self.user)

        second_user = create_user(
            email="test@test.com",
            password="testpass",
            is_staff=False,
        )
        second_user_borrowing = sample_borrowing(book, second_user)
        res = self.client.get(BORROWING_URL)

        serializer1 = BorrowingListSerializer(user_borrowing)
        serializer2 = BorrowingListSerializer(second_user_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)

    def test_filtering_by_user_id(self):
        book = sample_book()
        first_user = create_user(
            email="first@test.com", password="firstpass"
        )
        second_user = create_user(
            email="second@test.com", password="secondpass"
        )

        first_borrowing = sample_borrowing(book, first_user)
        second_borrowing = sample_borrowing(book, second_user)

        res = self.client.get(BORROWING_URL, {"user_id": f"{first_user.id}"})

        serializer1 = BorrowingListSerializer(first_borrowing)
        serializer2 = BorrowingListSerializer(second_borrowing)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)


class ReturnFunctionalityTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="test@test.com", password="testpass"
        )
        self.client.force_authenticate(self.user)

    def test_cannot_return_borrowing_twice(self):
        book = sample_book()
        borrowing = sample_borrowing(
            book, self.user, actual_return_date="2025-10-12"
        )
        url_for_return = return_url(borrowing.id)
        res = self.client.post(url_for_return, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_book_inventory_on_returning(self):
        book = sample_book()
        borrowing = sample_borrowing(
            book, self.user,
        )
        url_for_return = return_url(borrowing.id)

        res = self.client.post(url_for_return, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        get_after_transaction = Book.objects.get(id=book.id)

        self.assertEqual(get_after_transaction.inventory, book.inventory + 1)
