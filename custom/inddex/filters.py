from django.utils.translation import ugettext as _

from corehq.apps.reports.filters.base import BaseSingleOptionFilter, BaseMultipleOptionFilter
from custom.inddex.sqldata import FoodCodeData, FoodBaseTermData


class AgeRangeFilter(BaseSingleOptionFilter):
    slug = 'age_range'
    label = _('Age range')
    template = 'inddex/filters/age_filter.html'
    default_text = _('All')

    @property
    def options(self):
        return [
            (str(k), str(k)) for k in range(0, 5)
        ]


class AgeMonthsFilter(BaseSingleOptionFilter):
    slug = 'months'
    label = _('Months')
    default_text = '-'

    @property
    def options(self):
        return [
            # (str(k), str(k)) for k in range(1, 13)
            ('1', _('January')),
            ('2', _('February')),
            ('3', _('March')),
            ('4', _('April')),
            ('5', _('May')),
            ('6', _('June')),
            ('7', _('July')),
            ('8', _('August')),
            ('9', _('September')),
            ('10', _('October')),
            ('11', _('November')),
            ('12', _('December')),
        ]


class AgeYearsFilter(BaseSingleOptionFilter):
    slug = 'years'
    label = _('Years')
    default_text = '-'

    @property
    def options(self):
        return [
            (str(k), str(k)) for k in range(0, 11)
        ]


class GenderFilter(BaseSingleOptionFilter):
    slug = 'gender'
    label = _('Gender')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('male', _('Male')),
            ('female', _('Female'))
        ]


class SettlementAreaFilter(BaseSingleOptionFilter):
    slug = 'settlement'
    label = _('Settlement')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('urban', _('Urban')),
            ('rural', _('Rural'))
        ]


class BreastFeedingFilter(BaseSingleOptionFilter):
    slug = 'breast_feeding'
    label = _('Breast Feeding?')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('yes', _('Yes')),
            ('no', _('No'))
        ]


class SupplementsFilter(BaseMultipleOptionFilter):
    slug = 'supplements'
    label = _('Supplements')
    default_text = _('All')

    default_options = [
        'Supplement 1',
        'Supplement 2',
        'Supplement 3',
        'Supplement 4',
        'Supplement 5',
    ]

    @property
    def options(self):
        return [
            (option.lower(), _(option)) for option in self.default_options
        ]


class ExceptionDescriptionFilter(BaseSingleOptionFilter):
    slug = 'exception_description'
    label = _('Exception description')
    default_text = _('All')

    @property
    def exceptions_descriptions(self):
        return [
            ('missing', _('Error: Ingredient(s) are missing FCT info')),
            ('no_conversion', _('Error: No conversion factor available')),
            ('no_fct', _('Error: No FCT info available')),
            ('using_conversion', _('Info: Using conversion factor from the parent_food_code')),
            ('using_fct', _('Info: Using FCT from the parent_food_code'))
        ]

    @property
    def options(self):
        return [
            x for x in self.exceptions_descriptions
        ]


class ExceptionTypeFilter(BaseSingleOptionFilter):
    slug = 'exception_type'
    label = _('Exception type')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('error', _('Error')),
            ('info', _('Info'))
        ]


class FoodCodeFilter(BaseSingleOptionFilter):
    slug = 'food_code'
    label = _('Food Code')
    default_text = _('All')

    @property
    def food_codes(self):
        return FoodCodeData(config={'domain': self.domain}).rows

    @property
    def options(self):
        return [
            (str(x), str(x)) for x in self.food_codes
        ]


class FoodBaseTermFilter(BaseSingleOptionFilter):
    slug = 'food_base_term'
    label = _('Food base term')
    default_text = _('All')

    @property
    def food_base_terms(self):
        return FoodBaseTermData(config={'domain': self.domain}).rows

    @property
    def options(self):
        return [
            (x, _(x)) for x in self.food_base_terms
        ]


class FoodTypeFilter(BaseSingleOptionFilter):
    slug = 'food_type'
    label = _('Food type')
    default_text = _('All')

    @property
    def food_types(self):
        return [
            'food_item', 'non_std_food_item', 'non_std_recipe', 'std_recipe'
        ]

    @property
    def options(self):
        return [
            (x, x) for x in self.food_types
        ]
