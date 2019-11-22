from custom.inddex.filters import AgeRangeFilter, GenderFilter, SettlementAreaFilter, BreastFeedingFilter


class ReportBaseMixin:
    request = None

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
            'domain': obj.domain,
            'age_range': obj.age_range,
            'gender': obj.gender,
            'settlement': obj.settlement,
            'breast_feeding': obj.breast_feeding,
        }

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
