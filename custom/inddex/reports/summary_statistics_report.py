from memoized import memoized

from custom.inddex.ucr.data_providers.summary_statistics_data import SummaryStatsNutrientDataProvider, \
    SummaryStatsRespondentDataProvider
from custom.inddex.ucr.report_bases.summary_statistics_report import SummaryStatisticsReportBase


class SummaryStatisticsReport(SummaryStatisticsReportBase):
    default_rows = 10
    exportable = True

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        return [
            SummaryStatsNutrientDataProvider(config=config),
            SummaryStatsRespondentDataProvider(config=config)
        ]
