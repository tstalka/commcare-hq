from custom.inddex.filters import AgeRangeFilter, GenderFilter, SettlementAreaFilter, BreastFeedingFilter
from custom.inddex.ucr.report_bases.multi_tabular_report import MultiTabularReport
from custom.inddex.ucr.report_bases.report_base_mixin import ReportBaseMixin


class SummaryStatisticsReportBase(ReportBaseMixin, MultiTabularReport):
    title = 'Summary Statistics Report'
    name = 'Summary Statistics Reports'
    slug = 'summary_statistics_report'

    @property
    def fields(self):
        return self.get_base_fields()

    @property
    def report_config(self):
        return self.get_base_report_config(self)


