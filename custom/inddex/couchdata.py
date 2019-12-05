from memoized import memoized

from corehq.apps.fixtures.models import FixtureDataItem, FixtureDataType


@memoized
class CouchData:

    def __init__(self, domain, tables=None):
        self.domain = domain
        self.tables = {}
        for table in FixtureDataType.by_domain(domain=domain):
            if (tables and table.tag in tables) or not tables:
                self.tables[table.tag] = table.get_id

    @memoized
    def get_data_from_table(self, table_name=None, field=None, values=None, as_dict=False):
        data = []
        if table_name is None and len(self.tables) == 1:
            table_name = list(self.tables.keys())[0]
        elif not table_name:
            raise AttributeError('\'table_name\' must be specified')
        records = FixtureDataItem.by_data_type(self.domain, self.tables[table_name])
        if not field:
            return records

        for record in records:
            field_ = record.fields.get(field)
            if field_:
                field_list = field_.field_list
                if field_list:
                    if (values and field_list[0].field_value in values) or not values:
                        if as_dict:
                            data.append(self.record_to_dict(record))
                        else:
                            data.append(record)

        return data

    @staticmethod
    @memoized
    def record_to_dict(record):
        record_as_dict = {}
        fields = record.fields
        for field in fields:
            field_list = fields[field].field_list
            value = None if not field_list else field_list[0].field_value
            record_as_dict[field] = value

        return record_as_dict

    @memoized
    def as_dict(self, table_name=None, field=None, values=None):
        if field is None:
            field = 'food_code'
        messy_dicts = self.get_data_from_table(table_name=table_name, field=field, values=values, as_dict=True)
        clean_dicts = {}

        for messy_dict in messy_dicts:
            id_ = messy_dict[field]
            if id_ in clean_dicts:
                dict_ = self._get_dict(field, messy_dict)
                self._update_dict(clean_dicts[id_], dict_)
            else:
                clean_dicts[id_] = self._get_dict(field, messy_dict)

        return [
            [id_, values] for id_, values in clean_dicts.items()
        ]

    @staticmethod
    def _get_dict(id_key, dict_):
        dict_.pop(id_key)
        return dict_

    def _update_dict(self, old_dict, new_dict):
        new_keys = list(new_dict.keys())
        for key in new_keys:
            suffix = self._get_suffix(key, list(old_dict.keys()))
            if suffix == -1:
                old_dict[key] = new_dict
            if suffix == 1:
                old_dict[f'{key}_1'] = old_dict.pop(key)
                old_dict[f'{key}_2'] = new_dict[key]
            else:
                old_dict[f'{key}_{suffix}'] = new_dict[key]

    @staticmethod
    def _get_suffix(name, names):
        names.sort(reverse=True)
        names = [x for x in names]
        for n in names:
            if name == n:
                return 1
            elif n.startswith(name):
                if n[-1].isdigit():
                    return int(n[-1]) + 1

        return -1
