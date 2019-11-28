from memoized import memoized

from custom.inddex.filters import FoodCodeFilter
from custom.inddex.ucr.data_providers.exceptions_report_data import ExceptionReportDetailsData
from custom.inddex.ucr.report_bases.exceptions_report import ExceptionReportBase
from custom.inddex.utils import SingleTableReport


class ExceptionDetailsReport(ExceptionReportBase, SingleTableReport):
    title = 'Exception Details Report'
    name = title
    slug = 'exception_details_report'
    default_rows = 10
    exportable = True
    
    @property
    def fields(self):
        fields = super(ExceptionDetailsReport, self).fields
        if FoodCodeFilter not in fields:
            fields.insert(1, FoodCodeFilter)
        
        return fields

    @property
    def report_config(self):
        report_config = super(ExceptionDetailsReport, self).report_config
        report_config['food_code'] = self.food_code

        return report_config

    @property
    def food_code(self):
        return self.request.GET.get('food_code') or ''

    @property
    def headers(self):
        return ExceptionReportDetailsData(config=self.report_config).headers

    @property
    def rows(self):
        return ExceptionReportDetailsData(config=self.report_config).rows

