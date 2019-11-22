from custom.inddex.filters import ExceptionDescriptionFilter, FoodCodeFilter, FoodTypeFilter
from custom.inddex.ucr.report_bases.multi_tabular_report import MultiTabularReport


class ExceptionReportBase(MultiTabularReport):
    title = 'Exception Report'
    name = f'{title}s'
    slug = 'exception_report'

    @property
    def fields(self):
        return [
            ExceptionDescriptionFilter,
            FoodCodeFilter,
            FoodTypeFilter,
        ]

    @property
    def report_config(self):
        return {
            'exception_description': self.exception_description,
            'food_code': self.food_code,
            'food_type': self.food_type,
        }

    @property
    def exception_description(self):
        return self.request.GET.get('exception_description') or ''

    @property
    def food_code(self):
        return self.request.GET.get('food_code') or ''

    @property
    def food_type(self):
        return self.request.GET.get('food_type') or ''
