from django.contrib import admin

from recipes.models import Recipe, Ingredient, Tag, RecipeIngredient


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_of_additions',)
    readonly_fields = ('count_of_additions',)
    list_filter = ('author', 'name', 'tags',)
    fields = ('author', 'name', 'image', 'text', 'tags', 'cooking_time',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe',)
    fields = ('ingredient', 'recipe', 'amount',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
