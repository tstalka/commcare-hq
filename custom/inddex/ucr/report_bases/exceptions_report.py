from custom.inddex.ucr.report_bases.mixins import ExceptionReportBaseMixin
from custom.inddex.utils import SingleTableReport


class ExceptionReportBase(ExceptionReportBaseMixin, SingleTableReport):

    @property
    def fields(self):
        fields = super(ExceptionReportBase, self).fields
        fields += self.get_base_fields()

        return fields

    @property
    def report_config(self):
        report_config = super(ExceptionReportBase, self).report_config
        report_config.update(**self.get_base_report_config(self))

        return report_config

    @property
    def rows(self):
        return super(ExceptionReportBase, self).rows

    @property
    def headers(self):
        return super(ExceptionReportBase, self).headers
