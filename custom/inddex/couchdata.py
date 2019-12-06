from memoized import memoized

from corehq.apps.fixtures.models import FixtureDataItem, FixtureDataType


@memoized
class CouchData:

    def __init__(self, domain, tables=None):
        if not isinstance(tables, tuple):
            raise TypeError('\'tables\' must be a tuple')
        self.domain = domain
        self.tables = {}
        for table in FixtureDataType.by_domain(domain=domain):
            if (tables and table.tag in tables) or not tables:
                self.tables[table.tag] = table.get_id

    @memoized
    def get_data_from_table(self, table_name=None, fields=None, blank_fields=None, values=None, as_dict=False):
        data = []
        if table_name is None and len(self.tables) == 1:
            table_name = list(self.tables.keys())[0]
        elif not table_name:
            raise AttributeError('\'table_name\' must be specified')
        records = FixtureDataItem.by_data_type(self.domain, self.tables[table_name])
        if not fields:
            return records
        elif not isinstance(fields, tuple):
            raise TypeError('\'fields\' must be a tuple')
        if not blank_fields:
            blank_fields = tuple()
        if not isinstance(values, tuple):
            raise TypeError('\'values\' must be a tuple')
        values = {
            x[0]: x[1] for x in values
        }

        for record in records:
            invalid = False
            for field in fields:
                field_values = values[field]
                valid_record = self._check_values(record, field, field_values, blank_fields)
                if not valid_record:
                    invalid = True

            if as_dict and not invalid:
                data.append(self.record_to_dict(record))
            elif not invalid:
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
    def as_dict(self, table_name=None, key_field=None, additional_fields=None, blank_fields=None, values=None):
        if key_field is None:
            key_field = 'food_code'
        if not additional_fields:
            additional_fields = tuple()
        elif not isinstance(additional_fields, tuple):
            raise TypeError('\'additional_fields\' mus be a tuple')
        messy_dicts = self.get_data_from_table(
            table_name=table_name, fields=(key_field,)+additional_fields,
            blank_fields=blank_fields, values=values, as_dict=True
        )
        clean_dicts = {}

        for messy_dict in messy_dicts:
            id_ = messy_dict[key_field]
            if id_ in clean_dicts:
                dict_ = self._get_dict(key_field, messy_dict)
                self._update_dict(clean_dicts[id_], dict_)
            else:
                clean_dicts[id_] = self._get_dict(key_field, messy_dict)

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

    @staticmethod
    def _check_values(record, field, values, blank_fields):
        field_ = record.fields.get(field)
        if field_:
            field_list = field_.field_list
            if field_list:
                if (values and field_list[0].field_value in values) or not values:
                    return record
            elif not field_list and field in blank_fields:
                return record

        return False
