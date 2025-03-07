from collections import namedtuple
from datetime import date, datetime, timedelta

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from couchdbkit import ResourceNotFound
from memoized import memoized

from couchexport.export import SCALAR_NEVER_WAS
from dimagi.utils.dates import safe_strftime
from dimagi.utils.parsing import string_to_utc_datetime
from phonelog.models import UserErrorEntry

from corehq import toggles
from corehq.apps.app_manager.dbaccessors import (
    get_app,
    get_brief_apps_in_domain,
)
from corehq.apps.es import UserES, filters
from corehq.apps.es.aggregations import DateHistogram
from corehq.apps.hqwebapp.decorators import use_nvd3
from corehq.apps.locations.models import SQLLocation
from corehq.apps.locations.permissions import location_safe
from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.exceptions import BadRequestError
from corehq.apps.reports.filters.select import SelectApplicationFilter
from corehq.apps.reports.filters.users import ExpandedMobileWorkerFilter
from corehq.apps.reports.generic import (
    GenericTabularReport,
    GetParamsMixin,
    PaginatedReportMixin,
)
from corehq.apps.reports.standard import (
    ProjectReport,
    ProjectReportParametersMixin,
)
from corehq.apps.reports.util import format_datatables_data
from corehq.apps.users.util import user_display_string
from corehq.const import USER_DATE_FORMAT
from corehq.util.queries import paginated_queryset
from corehq.util.quickcache import quickcache


class DeploymentsReport(GenericTabularReport, ProjectReport, ProjectReportParametersMixin):
    """
    Base class for all deployments reports
    """


@location_safe
class ApplicationStatusReport(GetParamsMixin, PaginatedReportMixin, DeploymentsReport):
    name = ugettext_lazy("Application Status")
    slug = "app_status"
    emailable = True
    exportable = True
    exportable_all = True
    ajax_pagination = True
    fields = [
        'corehq.apps.reports.filters.users.ExpandedMobileWorkerFilter',
        'corehq.apps.reports.filters.select.SelectApplicationFilter'
    ]
    primary_sort_prop = None

    @property
    def headers(self):
        headers = DataTablesHeader(
            DataTablesColumn(_("Username"),
                             prop_name='username.exact',
                             sql_col='user_dim__username'),
            DataTablesColumn(_("Last Submission"),
                             prop_name='reporting_metadata.last_submissions.submission_date',
                             alt_prop_name='reporting_metadata.last_submission_for_user.submission_date',
                             sql_col='last_form_submission_date'),
            DataTablesColumn(_("Last Sync"),
                             prop_name='reporting_metadata.last_syncs.sync_date',
                             alt_prop_name='reporting_metadata.last_sync_for_user.sync_date',
                             sql_col='last_sync_log_date'),
            DataTablesColumn(_("Application"),
                             help_text=_("The name of the application from the user's last request."),
                             sortable=False),
            DataTablesColumn(_("Application Version"),
                             help_text=_("The application version from the user's last request."),
                             prop_name='reporting_metadata.last_builds.build_version',
                             alt_prop_name='reporting_metadata.last_build_for_user.build_version',
                             sql_col='last_form_app_build_version'),
            DataTablesColumn(_("CommCare Version"),
                             help_text=_("""The CommCare version from the user's last request"""),
                             prop_name='reporting_metadata.last_submissions.commcare_version',
                             alt_prop_name='reporting_metadata.last_submission_for_user.commcare_version',
                             sql_col='last_form_app_commcare_version'),
        )
        headers.custom_sort = [[1, 'desc']]
        return headers

    @property
    def default_sort(self):
        if self.selected_app_id:
            self.primary_sort_prop = 'reporting_metadata.last_submissions.submission_date'
            return {
                self.primary_sort_prop: {
                    'order': 'desc',
                    'nested_filter': {
                        'term': {
                            self.sort_filter: self.selected_app_id
                        }
                    }
                }
            }
        else:
            self.primary_sort_prop = 'reporting_metadata.last_submission_for_user.submission_date'
            return {'reporting_metadata.last_submission_for_user.submission_date': 'desc'}

    @property
    def sort_base(self):
        return '.'.join(self.primary_sort_prop.split('.')[:2])

    @property
    def sort_filter(self):
        return self.sort_base + '.app_id'

    def get_sorting_block(self):
        sort_prop_name = 'prop_name' if self.selected_app_id else 'alt_prop_name'
        res = []
        #the NUMBER of cols sorting
        sort_cols = int(self.request.GET.get('iSortingCols', 0))
        if sort_cols > 0:
            for x in range(sort_cols):
                col_key = 'iSortCol_%d' % x
                sort_dir = self.request.GET['sSortDir_%d' % x]
                col_id = int(self.request.GET[col_key])
                col = self.headers.header[col_id]
                sort_prop = getattr(col, sort_prop_name) or col.prop_name
                if x == 0:
                    self.primary_sort_prop = sort_prop
                if self.selected_app_id:
                    sort_dict = {
                        sort_prop: {
                            "order": sort_dir,
                            "nested_filter": {
                                "term": {
                                    self.sort_filter: self.selected_app_id
                                }
                            }
                        }
                    }
                else:
                    sort_dict = {sort_prop: sort_dir}
                res.append(sort_dict)
        if len(res) == 0 and self.default_sort is not None:
            res.append(self.default_sort)
        return res

    @property
    @memoized
    def selected_app_id(self):
        return self.request_params.get(SelectApplicationFilter.slug, None)

    @quickcache(['app_id'], timeout=60 * 60)
    def get_app_name(self, app_id):
        try:
            app = get_app(self.domain, app_id)
        except ResourceNotFound:
            pass
        else:
            return app.name

    def get_data_for_app(self, options, app_id):
        try:
            return list(filter(lambda option: option['app_id'] == app_id, options))[0]
        except IndexError:
            return {}

    @memoized
    def user_query(self, pagination=True):
        mobile_user_and_group_slugs = set(
            # Cater for old ReportConfigs
            self.request.GET.getlist('location_restricted_mobile_worker') +
            self.request.GET.getlist(ExpandedMobileWorkerFilter.slug)
        )
        user_query = ExpandedMobileWorkerFilter.user_es_query(
            self.domain,
            mobile_user_and_group_slugs,
            self.request.couch_user,
        )
        user_query = (user_query
                      .set_sorting_block(self.get_sorting_block()))
        if pagination:
            user_query = (user_query
                          .size(self.pagination.count)
                          .start(self.pagination.start))
        if self.selected_app_id:
            # adding nested filter for reporting_metadata.last_submissions.app_id
            # and reporting_metadata.last_syncs.app_id when app is selected
            last_submission_filter = filters.nested('reporting_metadata.last_submissions',
                                                    filters.term('reporting_metadata.last_submissions.app_id',
                                                                 self.selected_app_id)
                                                    )
            last_sync_filter = filters.nested('reporting_metadata.last_syncs',
                                              filters.term("reporting_metadata.last_syncs.app_id",
                                                           self.selected_app_id)
                                              )
            user_query = user_query.OR(last_submission_filter,
                                       last_sync_filter
                                       )
        return user_query

    def get_location_columns(self, grouped_ancestor_locs):
        from corehq.apps.locations.models import LocationType
        location_types = LocationType.objects.by_domain(self.domain)
        all_user_locations = grouped_ancestor_locs.values()
        all_user_loc_types = {loc.location_type_id for user_locs in all_user_locations for loc in user_locs}
        required_loc_columns = [loc_type for loc_type in location_types if loc_type.id in all_user_loc_types]
        return required_loc_columns

    def user_locations(self, ancestors, location_types):
        ancestors_by_type_id = {loc.location_type_id: loc.name for loc in ancestors}
        return [
            ancestors_by_type_id.get(location_type.id, '---')
            for location_type in location_types
        ]

    def get_bulk_ancestors(self, location_ids):
        """
        Returns the grouped ancestors for the location ids passed in the
        dictionary of following pattern
        {location_id_1: [self, parent, parent_of_parent,.,.,.,],
        location_id_2: [self, parent, parent_of_parent,.,.,.,],

        }
        :param domain: domain for which locations is to be pulled out
        :param location_ids: locations ids whose ancestors needs to be find
        :param kwargs: extra parameters
        :return: dict
        """
        where = Q(domain=self.domain, location_id__in=location_ids)
        location_ancestors = SQLLocation.objects.get_ancestors(where)
        location_by_id = {location.location_id: location for location in location_ancestors}
        location_by_pk = {location.id: location for location in location_ancestors}

        grouped_location = {}
        for location_id in location_ids:

            location_parents = []
            current_location = location_by_id[location_id].id if location_id in location_by_id else None

            while current_location is not None:
                location_parents.append(location_by_pk[current_location])
                current_location = location_by_pk[current_location].parent_id

            grouped_location[location_id] = location_parents

        return grouped_location

    def include_location_data(self):
        toggle = toggles.LOCATION_COLUMNS_APP_STATUS_REPORT
        return (
            (
                toggle.enabled(self.request.domain, toggles.NAMESPACE_DOMAIN)
                and self.rendered_as in ['export']
            )
        )

    def process_rows(self, users, fmt_for_export=False):
        rows = []
        users = list(users)

        if self.include_location_data():
            location_ids = {user['location_id'] for user in users if user['location_id']}
            grouped_ancestor_locs = self.get_bulk_ancestors(location_ids)
            self.required_loc_columns = self.get_location_columns(grouped_ancestor_locs)

        for user in users:
            last_build = last_seen = last_sub = last_sync = last_sync_date = app_name = commcare_version = None
            build_version = _("Unknown")
            reporting_metadata = user.get('reporting_metadata', {})
            if self.selected_app_id:
                last_submissions = reporting_metadata.get('last_submissions')
                if last_submissions:
                    last_sub = self.get_data_for_app(last_submissions, self.selected_app_id)
                last_syncs = reporting_metadata.get('last_syncs')
                if last_syncs:
                    last_sync = self.get_data_for_app(last_syncs, self.selected_app_id)
                    if last_sync is None:
                        last_sync = self.get_data_for_app(last_syncs, None)
                last_builds = reporting_metadata.get('last_builds')
                if last_builds:
                    last_build = self.get_data_for_app(last_builds, self.selected_app_id)
            else:
                last_sub = reporting_metadata.get('last_submission_for_user', {})
                last_sync = reporting_metadata.get('last_sync_for_user', {})
                last_build = reporting_metadata.get('last_build_for_user', {})
            if last_sub and last_sub.get('commcare_version'):
                commcare_version = _get_commcare_version(last_sub.get('commcare_version'))
            else:
                devices = user.get('devices', None)
                if devices:
                    device = max(devices, key=lambda dev: dev['last_used'])
                    if device.get('commcare_version', None):
                        commcare_version = _get_commcare_version(device['commcare_version'])
            if last_sub and last_sub.get('submission_date'):
                last_seen = string_to_utc_datetime(last_sub['submission_date'])
            if last_sync and last_sync.get('sync_date'):
                last_sync_date = string_to_utc_datetime(last_sync['sync_date'])
            if last_build:
                build_version = last_build.get('build_version') or build_version
                if last_build.get('app_id'):
                    app_name = self.get_app_name(last_build['app_id'])

            row_data = [
                user_display_string(user.get('username', ''),
                                    user.get('first_name', ''),
                                    user.get('last_name', '')),
                _fmt_date(last_seen, fmt_for_export), _fmt_date(last_sync_date, fmt_for_export),
                app_name or "---", build_version, commcare_version or '---'
            ]

            if self.include_location_data():
                location_data = self.user_locations(grouped_ancestor_locs.get(user['location_id'], []),
                                                    self.required_loc_columns)
                row_data = location_data + row_data

            rows.append(row_data)
        return rows

    def process_facts(self, app_status_facts, fmt_for_export=False):
        rows = []
        for fact in app_status_facts:
            rows.append([
                user_display_string(fact.user_dim.username,
                                    fact.user_dim.first_name,
                                    fact.user_dim.last_name),
                _fmt_date(fact.last_form_submission_date, fmt_for_export),
                _fmt_date(fact.last_sync_log_date, fmt_for_export),
                getattr(fact.app_dim, 'name', '---'),
                fact.last_form_app_build_version,
                fact.last_form_app_commcare_version
            ])
        return rows

    def get_sql_sort(self):
        res = None
        #the NUMBER of cols sorting
        sort_cols = int(self.request.GET.get('iSortingCols', 0))
        if sort_cols > 0:
            for x in range(sort_cols):
                col_key = 'iSortCol_%d' % x
                sort_dir = self.request.GET['sSortDir_%d' % x]
                col_id = int(self.request.GET[col_key])
                col = self.headers.header[col_id]
                if col.sql_col is not None:
                    res = col.sql_col
                    if sort_dir not in ('desc', 'asc'):
                        raise BadRequestError(
                            ('unexcpected sort direction: {}. '
                             'sort direction must be asc or desc'.format(sort_dir))
                        )
                    if sort_dir == 'desc':
                        res = '-{}'.format(res)
                    break
        if res is None:
            res = '-last_form_submission_date'
        return res

    @property
    def total_records(self):
        if self._total_records:
            return self._total_records
        else:
            return 0

    @property
    def rows(self):
        users = self.user_query().run()
        self._total_records = users.total
        return self.process_rows(users.hits)

    def get_user_ids(self):
        mobile_user_and_group_slugs = set(
            # Cater for old ReportConfigs
            self.request.GET.getlist('location_restricted_mobile_worker') +
            self.request.GET.getlist(ExpandedMobileWorkerFilter.slug)
        )
        user_ids = ExpandedMobileWorkerFilter.user_es_query(
            self.domain,
            mobile_user_and_group_slugs,
            self.request.couch_user,
        ).values_list('_id', flat=True)
        return user_ids

    @property
    def get_all_rows(self):
        users = self.user_query(False).scroll()
        self._total_records = self.user_query(False).count()
        return self.process_rows(users, True)

    @property
    def export_table(self):
        def _fmt_timestamp(timestamp):
            if timestamp is not None and timestamp >= 0:
                return safe_strftime(date.fromtimestamp(timestamp), USER_DATE_FORMAT)
            return SCALAR_NEVER_WAS

        result = super(ApplicationStatusReport, self).export_table
        table = list(result[0][1])
        location_colums = []

        if self.include_location_data():
            location_colums = ['{} Name'.format(loc_col.name.title()) for loc_col in self.required_loc_columns]

        table[0] = location_colums + table[0]

        for row in table[1:]:
            # Last submission
            row[len(location_colums) + 1] = _fmt_timestamp(row[len(location_colums) + 1])
            # Last sync
            row[len(location_colums) + 2] = _fmt_timestamp(row[len(location_colums) + 2])
        result[0][1] = table
        return result


def _get_commcare_version(app_version_info):
    commcare_version = (
        'CommCare {}'.format(app_version_info)
        if app_version_info
        else _("Unknown CommCare Version")
    )
    return commcare_version


def _choose_latest_version(*app_versions):
    """
    Chooses the latest version from a list of AppVersion objects - choosing the first one passed
    in with the highest version number.
    """
    usable_versions = [_f for _f in app_versions if _f]
    if usable_versions:
        return sorted(usable_versions, key=lambda v: v.build_version)[-1]


def _get_sort_key(date):
    if not date:
        return -1
    else:
        return int(date.strftime("%s"))


def _fmt_date(date, include_sort_key=True):
    def _timedelta_class(delta):
        return _bootstrap_class(delta, timedelta(days=7), timedelta(days=3))

    if not date:
        text = '<span class="label label-default">{0}</span>'.format(_("Never"))
    else:
        text = '<span class="{cls}">{text}</span>'.format(
                cls=_timedelta_class(datetime.utcnow() - date),
                text=_(_naturaltime_with_hover(date)),
        )
    if include_sort_key:
        return format_datatables_data(text, _get_sort_key(date))
    else:
        return text


def _naturaltime_with_hover(date):
    return '<span title="{}">{}</span>'.format(date, naturaltime(date) or '---')


def _bootstrap_class(obj, severe, warn):
    """
    gets a bootstrap class for an object comparing to thresholds.
    assumes bigger is worse and default is good.
    """
    if obj > severe:
        return "label label-danger"
    elif obj > warn:
        return "label label-warning"
    else:
        return "label label-success"


class ApplicationErrorReport(GenericTabularReport, ProjectReport):
    name = ugettext_lazy("Application Error Report")
    slug = "application_error"
    ajax_pagination = True
    sortable = False
    fields = ['corehq.apps.reports.filters.select.SelectApplicationFilter']

    # Filter parameters to pull from the URL
    model_fields_to_url_params = [
        ('app_id', SelectApplicationFilter.slug),
        ('version_number', 'version_number'),
    ]

    @classmethod
    def show_in_navigation(cls, domain=None, project=None, user=None):
        return user and toggles.APPLICATION_ERROR_REPORT.enabled(user.username)

    @property
    def shared_pagination_GET_params(self):
        shared_params = super(ApplicationErrorReport, self).shared_pagination_GET_params
        shared_params.extend([
            {'name': param, 'value': self.request.GET.get(param, None)}
            for model_field, param in self.model_fields_to_url_params
        ])
        return shared_params

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn(_("User")),
            DataTablesColumn(_("Expression")),
            DataTablesColumn(_("Message")),
            DataTablesColumn(_("Session")),
            DataTablesColumn(_("Application")),
            DataTablesColumn(_("App version")),
            DataTablesColumn(_("Date")),
        )

    @property
    @memoized
    def _queryset(self):
        qs = UserErrorEntry.objects.filter(domain=self.domain)
        for model_field, url_param in self.model_fields_to_url_params:
            value = self.request.GET.get(url_param, None)
            if value:
                qs = qs.filter(**{model_field: value})
        return qs

    @property
    def total_records(self):
        return self._queryset.count()

    @property
    @memoized
    def _apps_by_id(self):
        def link(app):
            return '<a href="{}">{}</a>'.format(
                reverse('view_app', args=[self.domain, app.get_id]),
                app.name,
            )
        return {
            app.get_id: link(app)
            for app in get_brief_apps_in_domain(self.domain)
        }

    def _ids_to_users(self, user_ids):
        users = (UserES()
                 .domain(self.domain)
                 .user_ids(user_ids)
                 .values('_id', 'username', 'first_name', 'last_name'))
        return {
            u['_id']: user_display_string(u['username'], u['first_name'], u['last_name'])
            for u in users
        }

    @property
    def rows(self):
        start = self.pagination.start
        end = start + self.pagination.count
        errors = self._queryset.order_by('-date')[start:end]
        users = self._ids_to_users({e.user_id for e in errors if e.user_id})
        for error in errors:
            yield [
                users.get(error.user_id, error.user_id),
                error.expr,
                error.msg,
                error.session,
                self._apps_by_id.get(error.app_id, error.app_id),
                error.version_number,
                str(error.date),
            ]


@location_safe
class AggregateUserStatusReport(ProjectReport, ProjectReportParametersMixin):
    slug = 'aggregate_user_status'

    report_template_path = "reports/async/aggregate_user_status.html"
    name = ugettext_lazy("Aggregate User Status")
    description = ugettext_lazy("See the last activity of your project's users in aggregate.")

    fields = [
        'corehq.apps.reports.filters.users.ExpandedMobileWorkerFilter',
    ]
    exportable = False
    emailable = False

    @use_nvd3
    def decorator_dispatcher(self, request, *args, **kwargs):
        super(AggregateUserStatusReport, self).decorator_dispatcher(request, *args, **kwargs)

    @memoized
    def user_query(self):
        # partially inspired by ApplicationStatusReport.user_query
        mobile_user_and_group_slugs = set(
            self.request.GET.getlist(ExpandedMobileWorkerFilter.slug)
        ) or set(['t__0'])  # default to all mobile workers on initial load
        user_query = ExpandedMobileWorkerFilter.user_es_query(
            self.domain,
            mobile_user_and_group_slugs,
            self.request.couch_user,
        )
        user_query = user_query.size(0)
        user_query = user_query.aggregations([
            DateHistogram('last_submission', 'reporting_metadata.last_submission_for_user.submission_date', '1d'),
            DateHistogram('last_sync', 'reporting_metadata.last_sync_for_user.sync_date', '1d')
        ])
        return user_query

    @property
    def template_context(self):

        class SeriesData(namedtuple('SeriesData', 'id title chart_color bucket_series help')):
            """
            Utility class containing everything needed to render the chart in a template.
            """

            def get_chart_data_series(self):
                return {
                    'key': _('Count of Users'),
                    'values': self.bucket_series.data_series,
                    'color': self.chart_color,
                }

            def get_chart_percent_series(self):
                return {
                    'key': _('Percent of Users'),
                    'values': self.bucket_series.percent_series,
                    'color': self.chart_color,
                }

            def get_buckets(self):
                return self.bucket_series.get_summary_data()


        class BucketSeries(namedtuple('Bucket', 'data_series total_series total user_count')):
            @property
            @memoized
            def percent_series(self):
                return [
                    {
                        'series': 0,
                        'x': row['x'],
                        'y': self._pct(row['y'], self.user_count)
                    }
                    for row in self.total_series
                ]

            def get_summary_data(self):
                def _readable_pct_from_total(total_series, index):
                    return '{0:.0f}%'.format(total_series[index - 1]['y'])

                return [
                    [_readable_pct_from_total(self.percent_series, 3), _('in the last 3 days')],
                    [_readable_pct_from_total(self.percent_series, 7), _('in the last week')],
                    [_readable_pct_from_total(self.percent_series, 30), _('in the last 30 days')],
                    [_readable_pct_from_total(self.percent_series, 60), _('in the last 60 days')],
                ]

            @property
            def total_percent(self):
                return '{0:.0f}%'.format(self._pct(self.total, self.user_count))

            @staticmethod
            def _pct(val, total):
                return (100. * float(val) / float(total)) if total else 0

        query = self.user_query().run()

        aggregations = query.aggregations
        last_submission_buckets = aggregations[0].raw_buckets
        last_sync_buckets = aggregations[1].raw_buckets
        total_users = query.total

        def _buckets_to_series(buckets, user_count):
            # start with N days of empty data
            # add bucket info to the data series
            # add last bucket
            days_of_history = 60
            vals = {
                i: 0 for i in range(days_of_history)
            }
            extra = total = running_total = 0
            today = datetime.today().date()
            for bucket_val in buckets:
                bucket_date = datetime.fromtimestamp(bucket_val['key'] / 1000.0).date()
                delta_days = (today - bucket_date).days
                val = bucket_val['doc_count']
                if delta_days in vals:
                    vals[delta_days] += val
                else:
                    extra += val
                total += val

            daily_series = []
            running_total_series = []

            for i in range(days_of_history):
                running_total += vals[i]
                daily_series.append(
                    {
                        'series': 0,
                        'x': '{}'.format(today - timedelta(days=i)),
                        'y': vals[i]
                    }
                )
                running_total_series.append(
                    {
                        'series': 0,
                        'x': '{}'.format(today - timedelta(days=i)),
                        'y': running_total
                    }
                )

            # catchall / last row
            daily_series.append(
                {
                    'series': 0,
                    'x': 'more than {} days ago'.format(days_of_history),
                    'y': extra,
                }
            )
            running_total_series.append(
                {
                    'series': 0,
                    'x': 'more than {} days ago'.format(days_of_history),
                    'y': running_total + extra,
                }
            )
            return BucketSeries(daily_series, running_total_series, total, user_count)



        submission_series = SeriesData(
            id='submission',
            title=_('Users who have Submitted'),
            chart_color='#004abf',
            bucket_series=_buckets_to_series(last_submission_buckets, total_users),
            help=_(
                "<strong>Aggregate Percents</strong> shows the percent of users who have submitted "
                "<em>since</em> a certain date.<br><br>"
                "<strong>Daily Counts</strong> shows the count of users whose <em>last submission was on</em> "
                "that particular day."
            )
        )
        sync_series = SeriesData(
            id='sync',
            title=_('Users who have Synced'),
            chart_color='#f58220',
            bucket_series=_buckets_to_series(last_sync_buckets, total_users),
            help=_(
                "<strong>Aggregate Percents</strong> shows the percent of users who have synced "
                "<em>since</em> a certain date.<br><br>"
                "<strong>Daily Counts</strong> shows the count of users whose <em>last sync was on</em> "
                "that particular day."
            )
        )
        context = super().template_context
        context.update({
            'submission_series': submission_series,
            'sync_series': sync_series,
            'total_users': total_users,
        })
        return context
