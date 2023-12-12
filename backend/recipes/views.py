import csv
from io import StringIO

import django_filters
from django import forms
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Purchase, Recipe,
                            RecipeIngredient, Tag)
from recipes.permissions import AuthAuthorOrReadOnly, OnlyOwnerPermission
from recipes.serializers import (CreateUpdateRecipeSerializer,
                                 FavoriteSerializer, IngredientSerializer,
                                 PurchaseSerializer, RecipeSerializer,
                                 TagSerializer)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.paginations import PageNumberLimitPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    pagination_class = None


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.CharFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'tags', 'author']

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value == '1':
            return queryset.filter(favorites__user=self.request.user)

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value == '1':
            return queryset.filter(purchases__user=self.request.user)

        return queryset


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (AuthAuthorOrReadOnly,)
    pagination_class = PageNumberLimitPagination
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_class

        return CreateUpdateRecipeSerializer

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        permission_classes=(OnlyOwnerPermission,),
        methods=['GET'],
        detail=False
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__purchases__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            ingredient_amount=Sum('amount')
        ).order_by('ingredient__name')

        result = list()
        for ingredient in ingredients:
            result.append([
                ingredient.get('ingredient__name'),
                ingredient.get('ingredient_amount'),
                ingredient.get('ingredient__measurement_unit')
            ]
            )

        try:
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerows(result)
            response = HttpResponse(
                csv_buffer.getvalue(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = \
                f'attachment; filename="my_cart_{request.user.username}"'

        except Exception as e:
            response = {
                'message': f'Ошибка при создании/отправке файла: {str(e)}'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        finally:
            csv_buffer.close()

        return response

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart', lookup_url_kwarg='pk')
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            result = self.preference_creator(PurchaseSerializer, pk, request)
            return Response(data=result.data, status=status.HTTP_201_CREATED)

        else:
            recipe_count, _ = self.preference_remover(Purchase, pk, request)
            if not recipe_count:
                return Response(
                    data={'errors': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            result = self.preference_creator(FavoriteSerializer, pk, request)
            return Response(data=result.data, status=status.HTTP_201_CREATED)

        else:
            recipe_count, _ = self.preference_remover(Favorite, pk, request)
            if not recipe_count:
                return Response(
                    data={'errors': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    def preference_creator(self, serializer_class, pk, request):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return serializer_class(instance)

    def preference_remover(self, model, pk, request):
        get_object_or_404(model, recipe_id=pk)
        recipe_count = model.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()
        return recipe_count


class IngredientFilter(django_filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
