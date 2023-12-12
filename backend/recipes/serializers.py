import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from recipes.models import (Favorite, Ingredient, Purchase, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from users.models import Subscription
from users.serializers import UserSerializer

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

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
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = (user.recipes.all()[:int(recipes_limit)]
                   if recipes_limit else user.recipes.all())
        return ShortRecipeSerializer(recipes, many=True).data


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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set', many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        return bool(
            self.context.get('request')
            and self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context.get('request').user,
                recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return bool(
            self.context.get('request')
            and self.context.get('request').user.is_authenticated
            and Purchase.objects.filter(
                user=self.context.get('request').user,
                recipe=obj).exists()
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CreateUpdateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateUpdateRecipeIngredientSerializer(
        source='recipeingredient_set', many=True
    )
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, attrs):
        ingredients = attrs.get('recipeingredient_set')
        tags = attrs.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )

        if not tags:
            raise serializers.ValidationError(
                'Список тэгов не может быть пустым'
            )

        self.check_duplicates(ingredients, 'ингредиенты')
        self.check_duplicates(tags, 'тэги')

        return attrs

    def check_duplicates(self, data, key_word):
        if not len(data) > 1:
            return data

        check_list = list()
        for item in data:
            if item in check_list:
                raise serializers.ValidationError(
                    f'Нельзя дублировать {key_word}'
                )

            check_list.append(item)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data)

        self.bind_ingresient_recipe(ingredients_data, recipe)

        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set')
        tags_data = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags_data)

        instance.ingredients.clear()
        self.bind_ingresient_recipe(ingredients_data, instance)

        instance.save()
        return super().update(instance, validated_data)

    def bind_ingresient_recipe(self, ingredients_data, recipe):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        return RecipeSerializer(instance).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, attrs):
        favorite_recipe = Favorite.objects.filter(
            user=attrs.get('user'), recipe_id=attrs.get('recipe')
        )
        if favorite_recipe.exists():
            raise serializers.ValidationError('Рецепт уже добавлен')

        return attrs

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance=instance.recipe).data


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ('user', 'recipe',)

    def validate(self, attrs):
        purchase_recipe = Purchase.objects.filter(
            user_id=attrs.get('user'), recipe_id=attrs.get('recipe')
        )
        if purchase_recipe.exists():
            raise serializers.ValidationError('Рецепт уже добавлен')

        return attrs

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance=instance.recipe).data
