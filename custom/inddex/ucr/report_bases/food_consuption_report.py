from memoized import memoized

from custom.inddex.ucr.data_providers.food_consumption_data import DetailedFoodConsumptionData, FoodConsumptionData
from custom.inddex.ucr.report_bases.multi_tabular_report import MultiTabularReport


class FoodConsumptionReportBase(MultiTabularReport):
    title = 'Food Consumption Report'
    name = f'{title} Reports'
    slug = 'food_consumption_report'

    @property
    def fields(self):
        return []
