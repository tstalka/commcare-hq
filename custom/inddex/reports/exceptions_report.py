from memoized import memoized

from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from custom.inddex.ucr.data_providers.exceptions_report_data import ExceptionReportDetailsData, ExceptionReportSummary
from custom.inddex.ucr.report_bases.exceptions_report import ExceptionReportBase


class ExceptionReport(ExceptionReportBase):
    default_rows = 10
    exportable = True

    @property
    @memoized
    def data_providers(self):
        config = self.report_config
        return [
            ExceptionReportDetailsData(config=config),
            ExceptionReportSummary(config=config)
        ]
