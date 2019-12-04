from custom.inddex.filters import FoodCodeFilter, ExceptionDescriptionFilter
from custom.inddex.ucr.data_providers.exceptions_report_data import ExceptionReportDetailsData
from custom.inddex.ucr.report_bases.exceptions_report import ExceptionReportBase


class ExceptionDetailsReport(ExceptionReportBase):
    title = 'Exception Details Report'
    name = title
    slug = 'exception_details_report'
    
    @property
    def fields(self):
        fields = super(ExceptionDetailsReport, self).fields
        for field in [FoodCodeFilter, ExceptionDescriptionFilter]:
            if field not in fields:
                fields.insert(1, field)
        
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

