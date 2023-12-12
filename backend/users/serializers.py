from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, user):
        return bool(
            self.context.get('request')
            and self.context.get('request').user.is_authenticated
            and Subscription.objects.filter(
                subscriber=self.context.get('request').user,
                subscribed_to=user).exists()
        )
