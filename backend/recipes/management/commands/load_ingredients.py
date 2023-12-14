import csv

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient

FILENAME = "ingredients.csv"


class Command(BaseCommand):
    help = "Load ingredients"

    def check_duplicate(self, row):
        return Ingredient.objects.filter(
            name=row[0],
            measurement_unit=row[1]
        ).exists()

    def handle(self, *args, **options):
        try:
            with open(
                    f'{settings.BASE_DIR}/../data/{FILENAME}', "r",
                    newline="", encoding='utf-8-sig'
            ) as file:
                reader = csv.reader(file)
                ingredients = [
                    Ingredient(
                        name=row[0],
                        measurement_unit=row[1]
                    ) for row in reader if not self.check_duplicate(row)
                ]

                Ingredient.objects.bulk_create(ingredients)

            self.stdout.write(self.style.SUCCESS('Success!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e.args}'))
