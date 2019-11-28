from custom.inddex.filters import FoodBaseTermFilter
from custom.inddex.ucr.data_providers.exceptions_report_data import ExceptionReportSummaryData
from custom.inddex.ucr.report_bases.exceptions_report import ExceptionReportBase


class ExceptionSummaryReport(ExceptionReportBase):
    title = 'Exception Details Summary'
    name = title
    slug = 'exception_details_summary'

    @property
    def fields(self):
        fields = super(ExceptionSummaryReport, self).fields
        if FoodBaseTermFilter not in fields:
            fields.insert(1, FoodBaseTermFilter)

        return fields

    @property
    def report_config(self):
        report_config = super(ExceptionSummaryReport, self).report_config
        report_config['food_code'] = self.food_base_term

        return report_config

    @property
    def food_base_term(self):
        return self.request.GET.get('food_base_term') or ''

    @property
    def headers(self):
        return ExceptionReportSummaryData(config=self.report_config).headers

    @property
    def rows(self):
        return ExceptionReportSummaryData(config=self.report_config).rows
