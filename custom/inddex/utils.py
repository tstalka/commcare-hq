from memoized import memoized

from corehq.apps.userreports.reports.util import ReportExport


class MultiSheetReportExport(ReportExport):

    def __init__(self, title, table_data):
        '''
        Allows to export multitabular reports in one xmlns file, different report tables are
        presented as different sheets in document

        :param title: Exported file title
        :param table_data: list of tuples, first element of tuple is sheet title, second is list of rows
        '''
        self.title = title
        self.table_data = table_data

    def build_export_data(self):
        sheets = []
        for name, rows in self.table_data:
            sheets.append([name, rows])
        return sheets

    @memoized
    def get_table(self):
        return self.build_export_data()
