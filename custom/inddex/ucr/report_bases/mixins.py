import datetime

from corehq.apps.reports.standard import DatespanMixin
from custom.inddex.filters import ExceptionDescriptionFilter, FoodTypeFilter, AgeRangeFilter, GenderFilter, \
    SettlementAreaFilter, BreastFeedingFilter
from custom.intrahealth.filters import DateRangeFilter
from dimagi.utils.dates import force_to_date


class ReportMixin(DatespanMixin):
    request = domain = None

    @property
    def fields(self):
        return [DateRangeFilter]

    @property
    def report_config(self):

        return {
            'domain': self.domain,
            'startdate': self.start_date,
            'enddate': self.end_date,
            # 'selected_location': self.selected_location
        }

    @property
    def start_date(self):
        start_date = self.request.GET.get('startdate')

        return start_date if start_date else str(datetime.datetime.now().date())

    @property
    def end_date(self):
        end_date = self.request.GET.get('end_date')

        return end_date if end_date else str(datetime.datetime.now().date())

    # @property
    # def selected_location(self):
    #     try:
    #         return SQLLocation.objects.get(location_id=self.request.GET.get('location_id'))
    #     except SQLLocation.DoesNotExist:
    #         return None


class BaseMixin:
    request = None

    @staticmethod
    def get_base_fields():
        raise NotImplementedError('\'get_base_fields\' must be implemented')

    @staticmethod
    def get_base_report_config(obj):
        raise NotImplementedError('\'get_report_config\' must be implemented')


class ReportBaseMixin(BaseMixin):

    @staticmethod
    def get_base_fields():
        return [
            AgeRangeFilter,
            GenderFilter,
            SettlementAreaFilter,
            BreastFeedingFilter,
        ]

    @staticmethod
    def get_base_report_config(obj):
        return {
            'age_range': obj.age_range,
            'gender': obj.gender,
            'settlement': obj.settlement,
            'breast_feeding': obj.breast_feeding,
        }

    @property
    def age_range(self):
        age_from = self.request.GET.get('age_from')
        age_to = self.request.GET.get('age_to')
        return age_from, age_to

    @property
    def gender(self):
        return self.request.GET.get('gender') or ''

    @property
    def settlement(self):
        return self.request.GET.get('settlement') or ''

    @property
    def breast_feeding(self):
        return self.request.GET.get('breast_feeding') or ''


class ExceptionReportBaseMixin(BaseMixin):

    @staticmethod
    def get_base_fields():
        return [
            FoodTypeFilter,
        ]

    @staticmethod
    def get_base_report_config(obj):
        return {
            'domain': obj.domain,
            'exception_description': obj.exception_description,
            'food_type': obj.food_type,
        }

    @property
    def exception_description(self):
        return self.request.GET.get('exception_description') or ''

    @property
    def food_type(self):
        return self.request.GET.get('food_type') or ''
