from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipes.views import (
    TagViewSet,
    RecipeViewSet,
    IngredientViewSet
)

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
