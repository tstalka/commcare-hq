from custom.inddex.ucr.data_providers.participant_consumption_report import ParticipantConsumptionReportData
from custom.inddex.ucr.report_bases.participant_consumption_report import ParticipantConsumptionReportBase


class ParticipantConsumptionReport(ParticipantConsumptionReportBase):
    title = 'Participant Consumption Report'
    name = title
    slug = 'participant_consumption_report'
    default_rows = 10
    exportable = True

    @property
    def report_context(self):
        if not self.needs_filters:
            return {
                'report': self.get_report_context(),
                'title': self.name
            }
        return {}

    @property
    def headers(self):
        return ParticipantConsumptionReportData(config=self.report_config).headers

    @property
    def rows(self):
        return ParticipantConsumptionReportData(config=self.report_config).rows

    def get_report_context(self):
        if self.needs_filters:
            headers = []
            rows = []
        else:
            rows = self.rows
            headers = self.headers

        context = {
            'report_table': {
                'title': self.name,
                'slug': self.slug,
                'headers': headers,
                'rows': rows,
                'default_rows': self.default_rows,
            }
        }

        return context
