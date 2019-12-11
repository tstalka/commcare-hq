from memoized import memoized

from custom.inddex.ucr.data_providers.gaps_summary_data import GapsSummaryMasterOutputData, ConvFactorGapsSummaryData, \
    FCTGapsSummaryData
from custom.inddex.ucr.report_bases.gaps_summary_report import GapsSummaryByFoodTypeBase


class GapsSummaryByFoodTypeReport(GapsSummaryByFoodTypeBase):

    @property
    def fields(self):
        return []

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        return [
            GapsSummaryMasterOutputData(config=config),
            ConvFactorGapsSummaryData(config=config),
            FCTGapsSummaryData(config=config)
        ]
