from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from corehq.apps.reports.sqlreport import SqlData


class SummaryStatsNutrientDataProvider(SqlData):
    total_row = None
    title = 'Summary stats per nutrient for total sample'
    slug = 'summary_statistics_report_nutrient'

    @property
    def engine_id(self):
        return 'ucr'

    headers = DataTablesHeader(
                DataTablesColumn('Nutrient'),
                DataTablesColumn('Mean'),
                DataTablesColumn('Median'),
                DataTablesColumn('Std.Dev'),
                DataTablesColumn('5_percent'),
                DataTablesColumn('25_percent'),
                DataTablesColumn('50_percent'),
                DataTablesColumn('75_percent'),
                DataTablesColumn('95_percent')
            )

    @property
    def rows(self):
        # TODO: calculate methods
        return [['n', 'm', 'm', 'std', 5, 25, 50, 75, 95]]


class SummaryStatsRespondentDataProvider(SqlData):
    total_row = None
    title = 'Summary stats per nutrient per respondent'
    slug = 'summary_statistics_report_respondent'

    @property
    def engine_id(self):
        return 'ucr'

    headers = DataTablesHeader(
                DataTablesColumn('Respondent'),
                DataTablesColumn('# of Recalls'),
                DataTablesColumn('Nutrient'),
                DataTablesColumn('Mean'),
                DataTablesColumn('Median'),
                DataTablesColumn('Std.Dev'),
                DataTablesColumn('5_percent'),
                DataTablesColumn('25_percent'),
                DataTablesColumn('50_percent'),
                DataTablesColumn('75_percent'),
                DataTablesColumn('95_percent')
            )

    @property
    def rows(self):
        # TODO: calculate methods
        return [['resp a', 2, 'n', 'm', 'm', 'std', 5, 25, 50, 75, 95]]
