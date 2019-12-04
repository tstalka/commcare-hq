from corehq.apps.reports.standard import DatespanMixin
from custom.inddex.filters import ExceptionDescriptionFilter, FoodTypeFilter, AgeRangeFilter, GenderFilter, \
    SettlementAreaFilter, BreastFeedingFilter
from custom.intrahealth.filters import DateRangeFilter


class ReportMixin(DatespanMixin):
    request = domain = None

    @property
    def fields(self):
        return [DateRangeFilter]

    @property
    def report_config(self):
        return {
            'domain': self.domain,
            'startdate': self.startdate,
            'enddate': self.enddate,
            # 'selected_location': self.selected_location
        }

    @property
    def startdate(self):
        return self.request.datespan.startdate

    @property
    def enddate(self):
        return self.request.datespan.end_of_end_day

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
