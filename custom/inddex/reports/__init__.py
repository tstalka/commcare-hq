from custom.inddex.reports.exception_report_details import ExceptionDetailsReport
from custom.inddex.reports.exceptions_report_summary import ExceptionSummaryReport
from custom.inddex.reports.nutrient_intakes import NutrientIntakesReport
from custom.inddex.reports.summary_statistics_report import SummaryStatisticsReport
from custom.inddex.reports.gaps_summary_by_food_type import GapsSummaryByFoodTypeReport

CUSTOM_REPORTS = (
    ('Custom Reports', (
        GapsSummaryByFoodTypeReport,
        ExceptionDetailsReport,
        ExceptionSummaryReport,
        NutrientIntakesReport,
        SummaryStatisticsReport
    )),
)
