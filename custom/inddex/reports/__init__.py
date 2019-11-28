from custom.inddex.reports.exception_report_details import ExceptionDetailsReport
from custom.inddex.reports.exceptions_report_summary import ExceptionSummaryReport
from custom.inddex.reports.food_consuption_report import FoodConsumptionReport
from custom.inddex.reports.participant_consumption_report import ParticipantConsumptionReport
from custom.inddex.reports.summary_statistics_report import SummaryStatisticsReport

CUSTOM_REPORTS = (
    ('Custom Reports', (
        FoodConsumptionReport,
        ParticipantConsumptionReport,
        ExceptionDetailsReport,
        ExceptionSummaryReport,
        SummaryStatisticsReport
    )),
)
