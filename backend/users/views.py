from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from serializers import (
    UserSerializer,
    UserCreateSerializer,
    SubscriptionSerializer
)

User = get_user_model()


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    http_method_names = [
        'get', 'post', 'head', 'options', 'delete'
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_class

        return UserCreateSerializer

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = self.serializer_class(
            request.user, context={'request': request}
        )
        return Response(data=serializer.data, status=HTTPStatus.OK)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        paginator = LimitOffsetPagination()
        result_page = paginator.paginate_queryset(
            request.user.subscriptions.all(), request
        )
        serializer = SubscriptionSerializer(
            result_page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        url_name='subscribe',
        lookup_url_kwarg='pk'
    )
    def subscribe(self, request, pk):
        candidate_user = get_object_or_404(User, pk=pk)
        if (
                request.user == candidate_user
                or candidate_user in request.user.subscriptions.all()
        ):
            return Response(
                data={"errors": "Действие запрещено(повторная подписка "
                                "или подписка на самого себя)"},
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            request.user.subscriptions.add(candidate_user)
            serializer = SubscriptionSerializer(
                candidate_user, context={'request': request}
            )
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        request.user.subscriptions.remove(candidate_user)
        return Response(status=status.HTTP_204_NO_CONTENT)
