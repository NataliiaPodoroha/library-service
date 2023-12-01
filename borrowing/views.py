from django.http import HttpResponseRedirect
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="return")
    def return_book(self, request, pk=None):
        borrowing = get_object_or_404(Borrowing, pk=pk)
        serializer = self.get_serializer(borrowing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if (payment_obj := borrowing.payments.filter(status="PENDING")).exists():
            return HttpResponseRedirect(payment_obj.first().session_url)

        serializer.save()

        return Response(
            {"message": "Borrowing returned successfully."}, status=status.HTTP_200_OK
        )
