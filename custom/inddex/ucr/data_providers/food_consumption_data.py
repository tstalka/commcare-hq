from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.sqlreport import SqlData


class DetailedFoodConsumptionData(SqlData):
    total_row = None
    title = 'Detailed Food Consumption Data'
    slug = 'detailed_food_consumption_data'

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('Food'),
                    DataTablesColumn('Calories'),
                    DataTablesColumn('Water'),
                )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
            ['egg', 1, 'yes'],
            ['leg', 2, 'a lot']
        ]


class FoodConsumptionData(SqlData):
    total_row = None
    title = 'Food Consumption Data'
    slug = 'food_consumption_data'

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('Detailed'),
                    DataTablesColumn('Food'),
                    DataTablesColumn('Calories'),
                    DataTablesColumn('Water'),
                )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
            ['yes', 'egg', 1, 'yes'],
            ['also yes', 'leg', 2, 'a lot']
        ]
