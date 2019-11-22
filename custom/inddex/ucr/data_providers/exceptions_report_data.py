from datetime import datetime

from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.sqlreport import SqlData


class ExceptionReportDetailsData(SqlData):
    total_row = None
    title = 'Exception Report Details'
    slug = 'exception_report_details'

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('Exception type'),
                    DataTablesColumn('Participant id'),
                    DataTablesColumn('Date'),
                    DataTablesColumn('Typed name'),
                    DataTablesColumn('Eating time'),
                    DataTablesColumn('Eating occasion'),
                    DataTablesColumn('Gift foodgroup code'),
                    DataTablesColumn('Gift foodgroup desc'),
                    DataTablesColumn('...')
                )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
                ['some type', 'participent', datetime.now(), 'bread', 'morning', 'snack', 'br4ad', 'wheat', '...'],
                ['some type', 'participent', datetime.now(), 'bread', 'morning', 'snack', 'br4ad', 'wheat', '...']
        ]


class ExceptionReportSummary(SqlData):
    total_row = None
    title = 'Exception Report Summary'
    slug = 'exception_report_summary'

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('Summary'),
                    DataTablesColumn('Exception type'),
                    DataTablesColumn('Participant id'),
                    DataTablesColumn('Date'),
                    DataTablesColumn('Typed name'),
                    DataTablesColumn('Eating time'),
                    DataTablesColumn('Eating occasion'),
                    DataTablesColumn('Gift foodgroup code'),
                    DataTablesColumn('Gift foodgroup desc'),
                    DataTablesColumn('...')
                )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
                ['summary','some type', 'participent', datetime.now(),
                 'bread', 'morning', 'snack', 'br4ad', 'wheat', '...'],
                ['summary', 'some type', 'participent', datetime.now(),
                 'bread', 'morning', 'snack', 'br4ad', 'wheat', '...']
        ]
