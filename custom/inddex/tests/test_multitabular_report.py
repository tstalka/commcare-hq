import json
from datetime import datetime, date

from django.test import RequestFactory
from django.urls import reverse
from mock import patch, PropertyMock

from corehq.apps.locations.models import SQLLocation
from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from custom.inddex.tests.test_utils import InddexTestCase
from custom.inddex.ucr.report_bases.multi_tabular_report import MultiTabularReport


class DateSpanMock:
    @property
    def startdate(self):
        return date(year=2010, month=10, day=10)

    @property
    def end_of_end_day(self):
        return date(year=2010, month=12, day=10)


class DataProviderMock:
    slug = 'provider_slug'
    title = 'report title'
    @property
    def rows(self):
        return [
            ['v1', 'v2'],
            ['v11', 'v22']
        ]

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('H1'),
                    DataTablesColumn('H2'),
                )


class MultitabularTest(InddexTestCase):

    @classmethod
    def setUpClass(cls):
        super(MultitabularTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(MultitabularTest, cls).tearDownClass()

    def build_request(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            path='/a/{}/reports/'.format(self.domain_name),
        )
        request.method = 'GET'
        request.couch_user = self.user
        request.GET = {'location_id': self.parent_location.location_id,
                       'filterSet': 'True'}
        request.__setattr__('datespan', DateSpanMock())
        return request

    def assertHeaders(self, h1, h2):
        h1_htmls = [header.html for header in h1.header]
        h2_htmls = [header.html for header in h2.header]
        self.assertEqual(h1_htmls, h2_htmls)

    def assertReportTable(self, context1, context2):
        self.assertHeaders(context1['headers'], context2['headers'])
        self.assertEqual(context1['rows'], context2['rows'])
        self.assertEqual(context1['title'], context2['title'])
        self.assertEqual(context1['slug'], context2['slug'])

    def test_creating_report_config(self):
        data = {
            'location_id': self.parent_location.location_id,
            'startdate': '2019-09-11',
            'enddate': '2019-09-11'
        }
        request = self.build_request()
        report = MultiTabularReport(request=request, domain=self.domain.name)
        actual_config = report.report_config
        expected_config = {'domain': self.domain.name,
                           'startdate': request.datespan.startdate,
                           'selected_location': self.parent_location,
                           'enddate': request.datespan.end_of_end_day}

        self.assertDictEqual(actual_config, expected_config)

    def test_getting_report_context(self):
        mocked_provider = DataProviderMock()
        with patch.object(MultiTabularReport, 'data_providers', new_callable=PropertyMock) \
            as mock_data_provider:
            mock_data_provider.return_value = [mocked_provider]
            request = self.build_request()
            report = MultiTabularReport(request=request, domain=self.domain.name)
            report.hide_filters = False
            actual_context = report.report_context
            expected_report_table = dict(
                    title=mocked_provider.title,
                    slug=mocked_provider.slug,
                    headers=mocked_provider.headers,
                    rows=mocked_provider.rows
                )

            self.assertEqual(actual_context['title'], report.title)
            self.assertReportTable(
                actual_context['reports'][0]['report_table'],
                expected_report_table
            )

