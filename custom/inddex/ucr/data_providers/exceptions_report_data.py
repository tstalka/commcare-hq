from datetime import datetime

from sqlagg.columns import SimpleColumn
from sqlagg.filters import EQ, GTE, LTE

from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.sqlreport import SqlData, DatabaseColumn
from custom.inddex.couchdata import CouchData
from custom.inddex.sqldata import FoodConsumptionDataSourceMixin, FoodCodeData


class ExceptionReportDetailsData(FoodConsumptionDataSourceMixin):
    total_row = None
    title = 'Exception Report Details'
    slug = 'exception_report_details'

    # a lot of headers, possibly some of them are in the wrong category, TODO: check it
    HEADERS_NAMES = {
        'ds': [
            'food_case_id', 'respondent_case_id', 'food_type', 'food_code', 'reference_food_code',
            'respondent_unique_id', 'short_name', 'food_name', 'eating_occasion', 'food_base_term', 'tag_1',
            'other_tag_1', 'tag_2', 'other_tag_2', 'tag_3', 'other_tag_3', 'tag_4', 'other_tag_4', 'tag_5',
            'other_tag_5', 'tag_6', 'other_tag_6', 'tag_7', 'other_tag_7', 'tag_8', 'other_tag_8', 'tag_9',
            'other_tag_9', 'tag_10', 'other_tag_10', 'conv_method', 'conv_method_desc', 'conv_option',
            'conv_option_desc', 'conv_size', 'conv_units', 'quantity',
        ],
        'not_ds': [
            'exception_type', 'exception_desc', 'recall_date', 'time_of_day', 'fao_who_gift_food_group_code',
            'fao_who_gift_food_group_description', 'user_food_group_description', 'nsr_conv_method_post_cooking',
            'nsr_conv_method_desc_post_cooking', 'nsr_conv_option_post_cooking', 'nsr_conv_option_desc_post_cooking',
            'nsr_conv_size_post_cooking', 'nsr_same_conv_method', 'nsr_consumed_cooked_ratio', 'conv_factor_used',
            'conv_factor_food_code', 'conv_factor_parent_food_code', 'fct_used', 'fct_food_code_exists',
            'fct_parent_food_code_exists', 'report_data_type', 'external_id',
        ]
    }

    def __init__(self, config):
        super(ExceptionReportDetailsData, self).__init__()
        self.config = config
        self.couch_db = CouchData(domain=config['domain'], tables=('conv_factors', 'food_composition_table'))

    @property
    def filters(self):
        filters = [GTE('date', 'startdate'), LTE('date', 'enddate')]
        for slug in ['food_code', 'food_type']:
            if self.config[slug]:
                filters.append(EQ(slug, slug))

        return filters

    @property
    def headers(self):
        headers = DataTablesHeader()
        for values in self.HEADERS_NAMES.values():
            for header in values:
                headers.add_column(DataTablesColumn(header))

        return headers

    @property
    def columns(self):
        columns = [
            DatabaseColumn(self._normalize_text(x), SimpleColumn(x)) for x in self.HEADERS_NAMES['ds'][1:]
        ]
        columns.insert(0, DatabaseColumn('Food code', SimpleColumn('doc_id')))

        return columns

    @property
    def group_by(self):
        group_by = [
            x for x in self.HEADERS_NAMES['ds'][1:]
        ]
        group_by.insert(0, 'doc_id')

        return group_by

    @property
    def rows(self):
        all_data = {}
        ds_data = self.get_data()

        for values in self.HEADERS_NAMES.values():
            for value in values:
                all_data[value] = []

        for row in ds_data:
            for key, value in row.items():
                if key == 'doc_id':
                    key = 'food_case_id'
                all_data[key].append(value)

        food_codes = all_data['food_code']
        fao_who_gift_food_group_code = self._fao_who_gift_food_group_code(
            [x for x in food_codes if x is not None], all_data['reference_food_code']
        )
        self._append_to_data_as_tuple(all_data, 'fao_who_gift_food_group_code', fao_who_gift_food_group_code)

        indexes = []
        for code in food_codes:
            index = food_codes.index(code)
            if code and all_data['food_type'][index] == 'std_recipe':
                indexes.append(index)

        # conv_factor_food_code will be needed later, but I was testing CouchData on it's query
        # TODO: should be probably a property
        values_ = (
            ('food_code', tuple(x for x in food_codes if food_codes.index(x) in indexes)),
            ('conv_method', tuple(x for x in all_data['conv_method'] if all_data['conv_method'].index(x) in indexes)),
            ('conv_option', tuple(x for x in all_data['conv_option']if all_data['conv_option'].index(x) in indexes))
        )
        conv_factor_food_code = self.couch_db.as_dict(
            table_name='conv_factors', key_field='food_code',
            additional_fields=('conv_method', 'conv_option'),
            blank_fields=('conv_option',), values=values_
        )
        self._append_to_data_as_tuple(all_data, 'conv_factor_food_code', conv_factor_food_code)

        # for now rows are returning only data fetched from ds
        return [x.values() for x in self.get_data()]

    @staticmethod
    def _normalize_text(text):
        return text.replace('_', ' ', text.count('_')).capitalize()

    @property
    def _food_code(self):
        food_code = self.config['food_code']
        if food_code:
            return tuple(food_code)
        else:
            return tuple(x[0] for x in FoodCodeData().rows)

    @staticmethod
    def _append_to_data_as_tuple(data, key, list_):
        for c in list_:
            data[key].append((c[0], c[1]))

    def _fao_who_gift_food_group_code(self, food_codes, parent_food_codes):
        fao_who_gift_food_group_code = self.couch_db.as_dict(
            table_name='food_composition_table', values=(('food_code', tuple(food_codes)),)
        )
        parent_codes = []
        for code in food_codes:
            if code not in [x[0] for x in fao_who_gift_food_group_code]:
                parent_codes.append(parent_food_codes[food_codes.index(code)])

        fao_who_gift_food_group_code += self.couch_db.as_dict(
            table_name='food_composition_table', values=(('food_code', tuple(parent_codes)),)
        )

        return [
            [x[0], {'fao_who_gift_food_group_code': x[1]['fao_who_gift_food_group_code']}]
            for x in fao_who_gift_food_group_code
        ]


class ExceptionReportSummaryData(SqlData):
    total_row = None
    title = 'Exception Report Summary'
    slug = 'exception_report_summary'

    @property
    def engine_id(self):
        return 'ucr'

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
            ['summary', 'some type', 'participent', datetime.now(),
             'bread', 'morning', 'snack', 'br4ad', 'wheat', '...'],
            ['summary', 'some type', 'participent', datetime.now(),
             'bread', 'morning', 'snack', 'br4ad', 'wheat', '...']
        ]
