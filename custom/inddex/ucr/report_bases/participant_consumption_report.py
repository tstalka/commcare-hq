from custom.inddex.filters import AgeMonthsFilter, AgeYearsFilter
from custom.inddex.ucr.report_bases.mixins import ReportBaseMixin
from custom.inddex.utils import SingleTableReport


class ParticipantConsumptionReportBase(ReportBaseMixin, SingleTableReport):
    title = 'Participant Consumption Report'
    name = title
    slug = 'participant_consumption_report'
    report_template_path = 'inddex/tabular_report.html'

    @property
    def fields(self):
        fields = super(ParticipantConsumptionReportBase, self).fields
        fields += self.get_base_fields()
        for age_filter in [AgeYearsFilter, AgeMonthsFilter]:
            if age_filter not in fields:
                fields.insert(1, age_filter)

        return fields

    @property
    def report_config(self):
        report_config = super(ParticipantConsumptionReportBase, self).report_config
        report_config.update(**self.get_base_report_config(self))
        report_config['months'] = self.age_months
        report_config['years'] = self.age_years

        return report_config

    @property
    def age_months(self):
        return self.request.GET.get('months') or ''

    @property
    def age_years(self):
        return self.request.GET.get('years') or ''

    @property
    def rows(self):
        return super(ParticipantConsumptionReportBase, self).rows

    @property
    def headers(self):
        return super(ParticipantConsumptionReportBase, self).headers


