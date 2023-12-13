import csv

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient

FILENAME = "ingredients.csv"


class Command(BaseCommand):
    help = "Load ingredients"

    def handle(self, *args, **options):
        try:
            with open(
                    f'{settings.BASE_DIR}/recipes/{FILENAME}', "r",
                    newline="", encoding='utf-8-sig'
            ) as file:
                reader = csv.reader(file)
                ingredients = [
                    Ingredient(
                        name=row[0],
                        measurement_unit=row[1]
                    ) for row in reader
                ]

                Ingredient.objects.bulk_create(ingredients)

            file.close()
            self.stdout.write(self.style.SUCCESS('Success!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e.args}'))
