from corehq.apps.reports.standard import CustomProjectReport
from custom.inddex.filters import AgeMonthsFilter, AgeYearsFilter
from custom.inddex.ucr.report_bases.report_base_mixin import ReportBaseMixin


class ParticipantConsumptionReportBase(ReportBaseMixin, CustomProjectReport):
    title = 'Participant Consumption Report'
    name = title
    slug = 'participant_consumption_report'
    report_template_path = "inddex/report_table.html"

    @property
    def fields(self):
        fields = self.get_base_fields()
        for age_filter in [AgeYearsFilter, AgeMonthsFilter]:
            if age_filter not in fields:
                fields.insert(0, age_filter)

        return fields

    @property
    def report_config(self):
        report_config = self.get_base_report_config(self)
        report_config['months'] = self.age_months
        report_config['years'] = self.age_years

        return report_config

    @property
    def age_months(self):
        return self.request.GET.get('months') or ''

    @property
    def age_years(self):
        return self.request.GET.get('years') or ''


