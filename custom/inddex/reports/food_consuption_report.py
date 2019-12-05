from memoized import memoized

from custom.inddex.ucr.data_providers.food_consumption_data import DetailedFoodConsumptionData, FoodConsumptionData, \
    ParticipantConsumptionReportData
from custom.inddex.ucr.report_bases.food_consuption_report import FoodConsumptionReportBase


class FoodConsumptionReport(FoodConsumptionReportBase):

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        return [
            DetailedFoodConsumptionData(config=config),
            FoodConsumptionData(config=config),
            ParticipantConsumptionReportData(config=config)
        ]
