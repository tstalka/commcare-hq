from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.reports.sqlreport import SqlData, DatabaseColumn
from sqlagg.columns import SimpleColumn
from sqlagg.filters import EQ

from corehq.apps.userreports.util import get_table_name
from custom.inddex.sqldata import FOOD_CONSUMPTION


class NutrientIntakesByFoodData(SqlData):
    total_row = None
    title = 'Nutrient Intakes By Food'
    slug = 'nutrient_intake_by_food_data'
    filters_config = None

    def __init__(self, config, filters_config):
        super(NutrientIntakesByFoodData, self).__init__()
        self.config = config
        self.filters_config = filters_config

    @property
    def table_name(self):
        return get_table_name(self.config['domain'], FOOD_CONSUMPTION)

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def columns(self):
        return [
            DatabaseColumn('doc_id', SimpleColumn('doc_id')),
            DatabaseColumn('respondent_case_id', SimpleColumn('respondent_case_id')),
            DatabaseColumn('opened_by_username', SimpleColumn('opened_by_username')),
            DatabaseColumn('owner_name', SimpleColumn('owner_name')),
            DatabaseColumn('respondent_unique_id', SimpleColumn('respondent_unique_id')),
            DatabaseColumn('gender', SimpleColumn('gender')),
            DatabaseColumn('age', SimpleColumn('age')),
            DatabaseColumn('supplements', SimpleColumn('supplements')),
            DatabaseColumn('urban_rural', SimpleColumn('urban_rural')),
            DatabaseColumn('pregnant', SimpleColumn('pregnant')),
            DatabaseColumn('breastfeeding', SimpleColumn('breastfeeding')),
            DatabaseColumn('food_code', SimpleColumn('food_code')),
            DatabaseColumn('reference_food_code', SimpleColumn('reference_food_code')),
            DatabaseColumn('food_type', SimpleColumn('food_type')),
            DatabaseColumn('include_in_analysis', SimpleColumn('include_in_analysis')),
            DatabaseColumn('food_status', SimpleColumn('food_status')),
            DatabaseColumn('eating_time', SimpleColumn('eating_time')),
            DatabaseColumn('date', SimpleColumn('date')),
            DatabaseColumn('eating_occasion', SimpleColumn('eating_occasion')),
            DatabaseColumn('already_reported_food', SimpleColumn('already_reported_food')),
            DatabaseColumn('already_reported_food_caseid', SimpleColumn('already_reported_food_caseid')),
            DatabaseColumn('is_ingredient', SimpleColumn('is_ingredient')),
            DatabaseColumn('ingr_recipe_case_id', SimpleColumn('ingr_recipe_case_id')),
            DatabaseColumn('ingr_recipe_code', SimpleColumn('ingr_recipe_code')),
            DatabaseColumn('short_name', SimpleColumn('short_name')),
            DatabaseColumn('food_name', SimpleColumn('food_name')),
            DatabaseColumn('recipe_name', SimpleColumn('recipe_name')),
            DatabaseColumn('food_base_term', SimpleColumn('food_base_term')),
            DatabaseColumn('tag_1', SimpleColumn('tag_1')),
            DatabaseColumn('other_tag_1', SimpleColumn('other_tag_1')),
            DatabaseColumn('tag_2', SimpleColumn('tag_2')),
            DatabaseColumn('other_tag_2', SimpleColumn('other_tag_2')),
            DatabaseColumn('tag_3', SimpleColumn('tag_3')),
            DatabaseColumn('other_tag_3', SimpleColumn('other_tag_3')),
            DatabaseColumn('tag_4', SimpleColumn('tag_4')),
            DatabaseColumn('other_tag_4', SimpleColumn('other_tag_4')),
            DatabaseColumn('tag_5', SimpleColumn('tag_5')),
            DatabaseColumn('other_tag_5', SimpleColumn('other_tag_5')),
            DatabaseColumn('tag_6', SimpleColumn('tag_6')),
            DatabaseColumn('other_tag_6', SimpleColumn('other_tag_6')),
            DatabaseColumn('tag_7', SimpleColumn('tag_7')),
            DatabaseColumn('other_tag_7', SimpleColumn('other_tag_7')),
            DatabaseColumn('tag_8', SimpleColumn('tag_8')),
            DatabaseColumn('other_tag_8', SimpleColumn('other_tag_8')),
            DatabaseColumn('tag_9', SimpleColumn('tag_9')),
            DatabaseColumn('other_tag_9', SimpleColumn('other_tag_9')),
            DatabaseColumn('tag_10', SimpleColumn('tag_10')),
            DatabaseColumn('other_tag_10', SimpleColumn('other_tag_10')),
            DatabaseColumn('conv_method', SimpleColumn('conv_method')),
            DatabaseColumn('conv_method_desc', SimpleColumn('conv_method_desc')),
            DatabaseColumn('conv_option', SimpleColumn('conv_option')),
            DatabaseColumn('conv_option_desc', SimpleColumn('conv_option_desc')),
            DatabaseColumn('conv_size', SimpleColumn('conv_size')),
            DatabaseColumn('conv_units', SimpleColumn('conv_units')),
            DatabaseColumn('quantity', SimpleColumn('quantity'))
        ]

    @property
    def headers(self):
        # TODO: we can try skip it!
        return DataTablesHeader(
                    DataTablesColumn('food_case_id'),
                    DataTablesColumn('respondent_case_id'),
                    DataTablesColumn('opened_by_username'),
                    DataTablesColumn('owner_name'),
                    DataTablesColumn('respondent_unique_id'),
                    DataTablesColumn('gender'),
                    DataTablesColumn('age'),
                    DataTablesColumn('supplements'),
                    DataTablesColumn('urban_rural'),
                    DataTablesColumn('pregnant'),
                    DataTablesColumn('breastfeeding'),
                    DataTablesColumn('food_code'),
                    DataTablesColumn('reference_food_code'),
                    DataTablesColumn('food_type'),
                    DataTablesColumn('include_in_analysis'),
                    DataTablesColumn('food_status'),
                    DataTablesColumn('eating_time'),
                    DataTablesColumn('date'),
                    DataTablesColumn('eating_occasion'),
                    DataTablesColumn('already_reported_food'),
                    DataTablesColumn('already_reported_food_case_id'),
                    DataTablesColumn('is_ingredient'),
                    DataTablesColumn('ingr_recipe_case_id'),
                    DataTablesColumn('ingr_recipe_code'),
                    DataTablesColumn('short_name'),
                    DataTablesColumn('food_name'),
                    DataTablesColumn('recipe_name'),
                    DataTablesColumn('food_base_term'),
                    DataTablesColumn('tag_1'),
                    DataTablesColumn('other_tag_1'),
                    DataTablesColumn('tag_2'),
                    DataTablesColumn('other_tag_2'),
                    DataTablesColumn('tag_3'),
                    DataTablesColumn('other_tag_3'),
                    DataTablesColumn('tag_4'),
                    DataTablesColumn('other_tag_4'),
                    DataTablesColumn('tag_5'),
                    DataTablesColumn('other_tag_5'),
                    DataTablesColumn('tag_6'),
                    DataTablesColumn('other_tag_6'),
                    DataTablesColumn('tag_7'),
                    DataTablesColumn('other_tag_7'),
                    DataTablesColumn('tag_8'),
                    DataTablesColumn('other_tag_8'),
                    DataTablesColumn('tag_9'),
                    DataTablesColumn('other_tag_9'),
                    DataTablesColumn('tag_10'),
                    DataTablesColumn('other_tag_10'),
                    DataTablesColumn('conv_method'),
                    DataTablesColumn('conv_method_desc'),
                    DataTablesColumn('conv_option'),
                    DataTablesColumn('conv_option_desc'),
                    DataTablesColumn('conv_size'),
                    DataTablesColumn('conv_units'),
                    DataTablesColumn('quantity')
                )

    @property
    def group_by(self):
        return ['doc_id', 'respondent_case_id', 'opened_by_username', 'owner_name', 'respondent_unique_id',
                'gender', 'age', 'supplements', 'urban_rural', 'pregnant', 'breastfeeding', 'food_code',
                'reference_food_code', 'food_type', 'include_in_analysis', 'food_status', 'eating_time',
                'date', 'eating_occasion', 'already_reported_food', 'already_reported_food_caseid',
                'is_ingredient', 'ingr_recipe_case_id', 'ingr_recipe_code', 'short_name', 'food_name',
                'recipe_name', 'food_base_term', 'tag_1', 'other_tag_1', 'tag_2', 'other_tag_2', 'tag_3',
                'other_tag_3', 'tag_4', 'other_tag_4', 'tag_5', 'other_tag_5', 'tag_6', 'other_tag_6',
                'tag_7', 'other_tag_7', 'tag_8', 'other_tag_8', 'tag_9', 'other_tag_9', 'tag_10', 'other_tag_10',
                'conv_method', 'conv_method_desc', 'conv_option', 'conv_option_desc', 'conv_size', 'conv_units',
                'quantity']

    @property
    def filters(self):
        filters = []
        print(self.filters_config['age_range'][0])
        if self.filters_config['gender']:
            filters.append(EQ('gender', 'gender'))
        if self.filters_config['pregnant']:
            filters.append(EQ('pregnant', 'pregnant'))
        if self.filters_config['breastfeeding']:
            filters.append(EQ('breastfeeding', 'breastfeeding'))
        if self.filters_config['urban_rural']:
            filters.append(EQ('urban_rural', 'urban_rural'))
        if self.filters_config['supplements']:
            filters.append(EQ('supplements', 'supplements'))
        if self.filters_config['recall_status']:
            filters.append(EQ('recall_status', 'recall_status'))
        return filters

    @property
    def filter_values(self):
        return self.filters_config

    @property
    def rows(self):
        result = []
        data_rows = self.get_data()
        group_columns = tuple(self.group_by)

        for row in data_rows:
            result.append([row[x] for x in group_columns])
        return result

class NutrientIntakesByRespondentData(SqlData):
    total_row = None
    title = 'Nutrient Intakes By Respondent'
    slug = 'nutrient_intakes_by_respondent'

    @property
    def engine_id(self):
        return 'ucr'

    @property
    def headers(self):
        return DataTablesHeader(
                    DataTablesColumn('Detailed'),
                    DataTablesColumn('Food'),
                    DataTablesColumn('Calories'),
                    DataTablesColumn('Water'),
                )

    @property
    def rows(self):
        # TODO: add proper calculations instead
        # It's worth to ensure that elements are of type DataTablesColumn instead of string
        return [
            ['yes', 'egg', 1, 'yes'],
            ['also yes', 'leg', 2, 'a lot']
        ]
