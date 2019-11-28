from custom.inddex.utils import MultiTabularReport


class FoodConsumptionReportBase(MultiTabularReport):
    title = 'Food Consumption Report'
    name = f'{title}s'
    slug = 'food_consumption_report'
    export_only = True
    show_filters = False

    @property
    def report_context(self):
        context = super(FoodConsumptionReportBase, self).report_context
        context['export_only'] = self.export_only

        return context

    @property
    def fields(self):
        return super(FoodConsumptionReportBase, self).fields

    @property
    def report_config(self):
        return super(FoodConsumptionReportBase, self).report_config

    @property
    def data_providers(self):
        raise super(FoodConsumptionReportBase, self).data_providers
