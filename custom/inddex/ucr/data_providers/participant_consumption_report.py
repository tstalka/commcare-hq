from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from corehq.apps.reports.sqlreport import SqlData


class ParticipantConsumptionReportData(SqlData):
    total_row = None
    title = 'Participant Consumption Report Data'
    slug = 'participant_consumption_report_data'

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn('Gender'),
            DataTablesColumn('Settlement'),
            DataTablesColumn('Breast feeding'),
            DataTablesColumn('Age'),
        )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
            ['M', 'U', 'N', 18],
            ['W', 'S', 'Y', 23]
        ]
