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


class SubscriptionRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('subscriber', 'subscribed_to',)

    def validate(self, attrs):
        if attrs.get('subscriber') == attrs.get('subscribed_to'):
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )

        subscription = Subscription.objects.filter(
            subscriber_id=attrs.get('subscriber'),
            subscribed_to_id=attrs.get('subscribed_to')
        )
        if subscription.exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя'
            )

        return attrs

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance=instance.subscribed_to,
            context=self.context).data


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, user):
        from recipes.serializers import ShortRecipeSerializer

        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = (user.recipes.all()[:int(recipes_limit)]
                   if recipes_limit else user.recipes.all())
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
