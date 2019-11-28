from django.utils.translation import ugettext as _

from corehq.apps.reports.filters.base import BaseSingleOptionFilter, BaseMultipleOptionFilter


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
    def options(self):
        return [
            ('Description 1', 'Description 1'),
            ('Description 2', 'Description 2')
        ]


class FoodCodeFilter(BaseSingleOptionFilter):
    slug = 'food_code'
    label = _('Food Code')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('Food Code 1', 'Food Code 1'),
            ('Food Code 2', 'Food Code 2')
        ]


class FoodBaseTermFilter(BaseSingleOptionFilter):
    slug = 'food_base_term'
    label = _('Food Base Term')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('Food Base Term 1', 'Food Base Term 1'),
            ('Food Base Term 2', 'Food Base Term 2')
        ]


class FoodTypeFilter(BaseSingleOptionFilter):
    slug = 'food_type'
    label = _('Food type')
    default_text = _('All')

    @property
    def options(self):
        return [
            ('Food type 1', 'Food type 1'),
            ('Food type 2', 'Food type 2')
        ]
