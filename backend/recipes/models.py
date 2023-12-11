from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()

MAX_LENGTH = 200
COLOR_MAX_LENGTH = 200


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH, verbose_name='Название', unique=True
    )
    color = ColorField(
        max_length=COLOR_MAX_LENGTH,
        verbose_name='Цвет',
        default='#FF0000',
        unique=True
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH, verbose_name='Слаг', unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['slug']


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH, verbose_name='Единицы измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'], name='ingredient_unique'
            )
        ]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публиуации'
    )
    name = models.CharField(max_length=MAX_LENGTH, verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes/images/', verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        'Ingredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        max_length=600,
        validators=[
            MinValueValidator(limit_value=1),
            MaxValueValidator(limit_value=600)
        ]
    )
    created_at = models.DateTimeField(
        verbose_name='Время добавления',
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['created_at']


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name='Количество')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient'
            )
        ]


class Preference(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return self.recipe.name

    class Meta:
        abstract = True


class Favorite(Preference):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='favorite_unique_user_recipe'
            )
        ]
        ordering = ['user', 'recipe']
        default_related_name = 'favorites'


class Purchase(Preference):
    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='purchase_unique_user_recipe'
            )
        ]
        ordering = ['user', 'recipe']
        default_related_name = 'purchases'
