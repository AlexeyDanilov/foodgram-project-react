import csv
import os

import django_filters
from django.http import HttpResponse
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from recipes.models import Tag, Recipe, Ingredient, Purchase, Favorite
from recipes.permissions import RecipeActionPermission, OnlyOwnerPermission
from serializers import (
    TagSerializer,
    RecipeSerializer,
    CreateUpdateRecipeSerializer,
    AddRecipeSerializer,
    IngredientSerializer
)


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    pagination_class = None
    http_method_names = ['get']


class RecipeFilter(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        _filter = dict()
        if 'is_favorited' in request.GET:
            _filter['favorite__isnull'] = not bool(
                request.GET.get('is_favorited')
            )

        if 'is_in_shopping_cart' in request.GET:
            _filter['purchase__isnull'] = not bool(
                request.GET.get('is_in_shopping_cart')
            )

        if 'tags' in request.GET:
            _filter['tags__slug__in'] = request.GET.getlist('tags')

        if 'author' in request.GET:
            _filter['author__id'] = request.GET.get('author')

        return queryset.filter(**_filter).distinct()


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (RecipeActionPermission,)
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend, RecipeFilter]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_class

        return CreateUpdateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        permission_classes=(OnlyOwnerPermission,),
        methods=['GET'],
        detail=False
    )
    def download_shopping_cart(self, request):
        recipes_ids = request.user.purchase_set.values_list(
            'recipe_id', flat=True
        )
        ingredients = Recipe.objects.filter(pk__in=recipes_ids).values(
            'recipeingredient__ingredient__id',
            'recipeingredient__ingredient__name',
            'recipeingredient__ingredient__measurement_unit',
            'recipeingredient__amount'
        )

        result = dict()
        for ingredient in ingredients:
            if result.get(ingredient.get('recipeingredient__ingredient__id')):
                result[
                    ingredient.get('recipeingredient__ingredient__id')
                ][2] += ingredient.get('recipeingredient__amount')

            else:
                result[ingredient.get('recipeingredient__ingredient__id')] = [
                    ingredient.get('recipeingredient__ingredient__name'),
                    ingredient.get(
                        'recipeingredient__ingredient__measurement_unit'
                    ),
                    ingredient.get('recipeingredient__amount')
                ]

        file_path = os.path.join('/', f'my_cart_{request.user.username}')

        try:
            with open(file_path, 'w', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(result.values())

            with open(file_path, 'rb') as file:
                response = HttpResponse(
                    file.read(),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = \
                    f'attachment; filename="my_cart_{request.user.username}"'

            os.remove(file_path)

            return response
        except Exception as e:
            response = {
                'message': f'Ошибка при создании/отправке файла: {str(e)}'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart', lookup_url_kwarg='pk')
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            added_recipe = Purchase.objects.create(
                user=request.user, recipe_id=pk
            )
            serializer = AddRecipeSerializer(added_recipe.recipe)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        else:
            added_recipe = Purchase.objects.filter(
                user=request.user, recipe_id=pk
            ).first()
            added_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            added_recipe, created = Favorite.objects.get_or_create(
                user=request.user, recipe_id=pk
            )
            if not created:
                return Response(
                    data={'errors': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = AddRecipeSerializer(added_recipe.recipe)
            return Response(data=result.data, status=status.HTTP_201_CREATED)

        else:
            added_recipe = Favorite.objects.filter(
                user=request.user, recipe_id=pk
            ).first()
            added_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientFilter(django_filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='startswith')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class IngredientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None
    http_method_names = ['get']
