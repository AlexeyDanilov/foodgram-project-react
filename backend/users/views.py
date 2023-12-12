from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as UVS
from recipes.serializers import (SubscriptionRelatedSerializer,
                                 SubscriptionSerializer)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription
from users.paginations import PageNumberLimitPagination
from users.serializers import UserSerializer

User = get_user_model()


class UserViewSet(UVS):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    pagination_class = PageNumberLimitPagination
    lookup_field = 'pk'
    http_method_names = [
        'get', 'post', 'head', 'options', 'delete'
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_class

        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ('me', 'subscriptions', 'subscribe',):
            return [IsAuthenticated(), ]

        return [AllowAny(), ]

    @action(
        methods=['get'],
        detail=False,
    )
    def subscriptions(self, request):
        paginator = PageNumberLimitPagination()
        subscriptions = Subscription.objects.filter(subscriber=request.user)
        subscribed_to_users = [
            subscription.subscribed_to for subscription in subscriptions
        ]
        result_page = paginator.paginate_queryset(
            subscribed_to_users,
            request
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
        lookup_url_kwarg='pk',
    )
    def subscribe(self, request, pk):
        get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            data = {
                'subscriber': request.user.id,
                'subscribed_to': pk
            }
            serializer = SubscriptionRelatedSerializer(
                data=data
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            result = SubscriptionRelatedSerializer(
                instance, context={'request': request}
            )
            return Response(data=result.data, status=status.HTTP_201_CREATED)

        subscription_count, _ = Subscription.objects.filter(
            subscriber=request.user.id,
            subscribed_to=pk
        ).delete()
        if not subscription_count:
            return Response(
                data={'errors': 'Ошибка отписки'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
