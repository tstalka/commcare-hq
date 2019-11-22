from memoized import memoized

from corehq.apps.locations.models import SQLLocation
from corehq.apps.reports.filters.dates import DatespanFilter
from corehq.apps.reports.filters.fixtures import AsyncLocationFilter
from corehq.apps.reports.generic import GenericTabularReport
from corehq.apps.reports.standard import CustomProjectReport
from custom.inddex.utils import MultiSheetReportExport


class MultiTabularReport(CustomProjectReport, GenericTabularReport):
    title = 'Multi report'
    name = 'Multi Report'
    slug = 'multi_report'
    report_template_path = "inddex/multi_report.html"
    flush_layout = True

    @property
    def fields(self):
        return []

    @property
    @memoized
    def data_providers(self):
        return []

    @property
    def report_context(self):
        context = {
            'reports': [self.get_report_context(dp) for dp in self.data_providers],
            'title': self.title
        }

        return context

    @property
    @memoized
    def report_export(self):
        prepared_data = [self.format_table_to_export(dp) for dp in self.data_providers]
        return MultiSheetReportExport(self.title, prepared_data)

    @property
    def export_table(self):
        return self.report_export.get_table()

    def get_report_context(self, data_provider):
        self.data_source = data_provider
        if self.needs_filters:
            headers = []
            rows = []
        else:
            rows = data_provider.rows
            headers = data_provider.headers

        context = dict(
            report_table=dict(
                title=data_provider.title,
                slug=data_provider.slug,
                headers=headers,
                rows=rows
            )
        )

        return context

    def format_table_to_export(self, data_provider):
        exported_rows = [[header.html for header in data_provider.headers]]
        exported_rows.extend(data_provider.rows)
        title = data_provider.slug
        return title, exported_rows

    @property
    def report_config(self):
        return {
            'domain': self.domain,
            'startdate': self.startdate,
            'enddate': self.enddate,
            'selected_location': self.selected_location
        }

    @property
    def startdate(self):
        return self.request.datespan.startdate

    @property
    def enddate(self):
        return self.request.datespan.end_of_end_day

    @property
    def selected_location(self):
        try:
            return SQLLocation.objects.get(location_id=self.request.GET.get('location_id'))
        except SQLLocation.DoesNotExist:
            return None
