from colorfield.fields import ColorField
from django.contrib import admin
from recipes.models import Ingredient, Recipe, Tag


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_of_additions',)
    readonly_fields = ('count_of_additions',)
    list_filter = ('author', 'name', 'tags',)
    fields = (
        'author',
        'name',
        'image',
        'text',
        'tags',
        'cooking_time',
        'count_of_additions',
    )

    def count_of_additions(self, obj):
        return obj.favorite_set.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    formfield_overrides = {
        ColorField: {'widget': admin.widgets.AdminTextInputWidget},
    }


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
