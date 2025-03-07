from dateutil.relativedelta import relativedelta

from custom.icds_reports.const import AGG_CHILD_HEALTH_PNC_TABLE
from custom.icds_reports.utils.aggregation_helpers import month_formatter
from custom.icds_reports.utils.aggregation_helpers.distributed.base import (
    StateBasedAggregationDistributedHelper,
)


class PostnatalCareFormsChildHealthAggregationDistributedHelper(StateBasedAggregationDistributedHelper):
    helper_key = 'postnatal-care-forms-child-health'
    ucr_data_source_id = 'static-postnatal_care_forms'
    aggregate_parent_table = AGG_CHILD_HEALTH_PNC_TABLE

    def data_from_ucr_query(self):
        current_month_start = month_formatter(self.month)
        next_month_start = month_formatter(self.month + relativedelta(months=1))

        return """
        SELECT DISTINCT child_health_case_id AS case_id,
        supervisor_id AS supervisor_id,
        %(current_month_start)s as month,
        LAST_VALUE(timeend) OVER w AS latest_time_end,
        MAX(counsel_increase_food_bf) OVER w AS counsel_increase_food_bf,
        MAX(counsel_breast) OVER w AS counsel_breast,
        MAX(skin_to_skin) OVER w AS skin_to_skin,
        LAST_VALUE(is_ebf) OVER w AS is_ebf,
        LAST_VALUE(water_or_milk) OVER w AS water_or_milk,
        LAST_VALUE(other_milk_to_child) OVER w AS other_milk_to_child,
        LAST_VALUE(tea_other) OVER w AS tea_other,
        LAST_VALUE(eating) OVER w AS eating,
        MAX(counsel_exclusive_bf) OVER w AS counsel_exclusive_bf,
        MAX(counsel_only_milk) OVER w AS counsel_only_milk,
        MAX(counsel_adequate_bf) OVER w AS counsel_adequate_bf,
        LAST_VALUE(not_breastfeeding) OVER w AS not_breastfeeding
        FROM "{ucr_tablename}"
        WHERE timeend >= %(current_month_start)s AND
              timeend < %(next_month_start)s AND
              state_id = %(state_id)s AND
              child_health_case_id IS NOT NULL
        WINDOW w AS (
            PARTITION BY supervisor_id, child_health_case_id
            ORDER BY timeend RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )
        """.format(ucr_tablename=self.ucr_tablename), {
            "current_month_start": current_month_start,
            "next_month_start": next_month_start,
            "state_id": self.state_id
        }

    def aggregation_query(self):
        month = self.month.replace(day=1)
        previous_month = month - relativedelta(months=1)

        ucr_query, ucr_query_params = self.data_from_ucr_query()
        query_params = {
            "month": month_formatter(month),
            "state_id": self.state_id,
            "previous_month": previous_month
        }
        query_params.update(ucr_query_params)

        return """
        INSERT INTO "{tablename}" (
          state_id, supervisor_id, month, case_id, latest_time_end_processed, counsel_increase_food_bf,
          counsel_breast, skin_to_skin, is_ebf, water_or_milk, other_milk_to_child,
          tea_other, eating, counsel_exclusive_bf, counsel_only_milk, counsel_adequate_bf,
          not_breastfeeding
        ) (
          SELECT
            %(state_id)s AS state_id,
            COALESCE(ucr.supervisor_id, prev_month.supervisor_id) AS supervisor_id,
            %(month)s AS month,
            COALESCE(ucr.case_id, prev_month.case_id) AS case_id,
            GREATEST(ucr.latest_time_end, prev_month.latest_time_end_processed)
                AS latest_time_end_processed,
            GREATEST(ucr.counsel_increase_food_bf, prev_month.counsel_increase_food_bf)
                AS counsel_increase_food_bf,
            GREATEST(ucr.counsel_breast, prev_month.counsel_breast) AS counsel_breast,
            GREATEST(ucr.skin_to_skin, prev_month.skin_to_skin) AS skin_to_skin,
            ucr.is_ebf AS is_ebf,
            ucr.water_or_milk AS water_or_milk,
            ucr.other_milk_to_child AS other_milk_to_child,
            ucr.tea_other AS tea_other,
            ucr.eating AS eating,
            GREATEST(ucr.counsel_exclusive_bf, prev_month.counsel_exclusive_bf) AS counsel_exclusive_bf,
            GREATEST(ucr.counsel_only_milk, prev_month.counsel_only_milk) AS counsel_only_milk,
            GREATEST(ucr.counsel_adequate_bf, prev_month.counsel_adequate_bf) AS counsel_adequate_bf,
            ucr.not_breastfeeding AS not_breastfeeding
          FROM ({ucr_table_query}) ucr
          FULL OUTER JOIN (
             SELECT * FROM "{tablename}" WHERE month = %(previous_month)s AND state_id = %(state_id)s
          ) prev_month
          ON ucr.case_id = prev_month.case_id AND ucr.supervisor_id = prev_month.supervisor_id
          WHERE coalesce(ucr.month, %(month)s) = %(month)s
            AND coalesce(prev_month.month, %(previous_month)s) = %(previous_month)s
            AND coalesce(prev_month.state_id, %(state_id)s) = %(state_id)s
        )
        """.format(
            ucr_table_query=ucr_query,
            tablename=self.aggregate_parent_table
        ), query_params
