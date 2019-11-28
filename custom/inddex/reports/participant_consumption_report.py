from custom.inddex.ucr.data_providers.participant_consumption_report import ParticipantConsumptionReportData
from custom.inddex.ucr.report_bases.participant_consumption_report import ParticipantConsumptionReportBase


class ParticipantConsumptionReport(ParticipantConsumptionReportBase):

    @property
    def headers(self):
        return ParticipantConsumptionReportData(config=self.report_config).headers

    @property
    def rows(self):
        return ParticipantConsumptionReportData(config=self.report_config).rows
