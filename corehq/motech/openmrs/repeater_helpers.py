import re
from collections import defaultdict

from django.utils.translation import ugettext as _

from lxml import html
from requests import RequestException
from urllib3.exceptions import HTTPError

from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.xform import extract_case_blocks

from corehq.apps.case_importer import util as importer_util
from corehq.apps.case_importer.const import LookupErrors
from corehq.apps.hqcase.utils import submit_case_blocks
from corehq.form_processor.interfaces.dbaccessors import CaseAccessors
from corehq.motech.const import DIRECTION_EXPORT
from corehq.motech.openmrs.const import (
    ADDRESS_PROPERTIES,
    LOCATION_OPENMRS_UUID,
    NAME_PROPERTIES,
    PERSON_PROPERTIES,
    PERSON_UUID_IDENTIFIER_TYPE_ID,
    XMLNS_OPENMRS,
)
from corehq.motech.openmrs.exceptions import (
    DuplicateCaseMatch,
    OpenmrsConfigurationError,
    OpenmrsException,
    OpenmrsHtmlUiChanged,
)
from corehq.motech.openmrs.finders import PatientFinder
from corehq.motech.requests import Requests
from corehq.motech.value_source import (
    CaseTriggerInfo,
    get_ancestor_location_metadata_value,
    get_case_location,
)
from corehq.util.quickcache import quickcache


def get_case_location_ancestor_repeaters(case):
    """
    Determine the location of the case's owner, and search up its
    ancestors to find the first OpenMRS Repeater(s).

    Returns a list because more than one OpenmrsRepeater may have the
    same location.
    """
    from corehq.motech.openmrs.repeaters import OpenmrsRepeater

    case_location = get_case_location(case)
    if not case_location:
        return []
    location_repeaters = defaultdict(list)
    for repeater in OpenmrsRepeater.by_domain(case.domain):
        if repeater.location_id:
            location_repeaters[repeater.location_id].append(repeater)
    for location_id in reversed(case_location.path):
        if location_id in location_repeaters:
            return location_repeaters[location_id]
    return []


def get_ancestor_location_openmrs_uuid(case):
    location = get_case_location(case)
    if location:
        return get_ancestor_location_metadata_value(location, LOCATION_OPENMRS_UUID)


def search_patients(requests, search_string):
    response = requests.get('/ws/rest/v1/patient', {'q': search_string, 'v': 'full'}, raise_for_status=True)
    return response.json()


def get_patient_by_uuid(requests, uuid):
    if not uuid:
        return None
    if not re.match(r'^[a-fA-F0-9\-]{36}$', uuid):
        # UUID should come from OpenMRS. If this ever happens we want to know about it.
        raise ValueError('Person UUID "{}" failed validation'.format(uuid))
    response = requests.get('/ws/rest/v1/patient/' + uuid, {'v': 'full'}, raise_for_status=True)
    return response.json()


def get_patient_by_identifier(requests, identifier_type_uuid, value):
    """
    Return the patient that matches the given identifier. If the
    number of matches is zero or more than one, return None.
    """
    response_json = search_patients(requests, value)
    patients = []
    for patient in response_json['results']:
        for identifier in patient['identifiers']:
            if (
                identifier['identifierType']['uuid'] == identifier_type_uuid and
                identifier['identifier'] == value
            ):
                patients.append(patient)
    try:
        patient, = patients
    except ValueError:
        return None
    else:
        return patient


def get_patient_by_id(requests, patient_identifier_type, patient_identifier):
    # Fetching the patient is the first request sent to the server. If
    # there is a mistake in the server details, or the server is
    # offline, this is where we will discover it.
    if not patient_identifier:
        # The case property has no value
        return None
    try:
        if patient_identifier_type == PERSON_UUID_IDENTIFIER_TYPE_ID:
            return get_patient_by_uuid(requests, patient_identifier)
        else:
            return get_patient_by_identifier(requests, patient_identifier_type, patient_identifier)
    except (RequestException, HTTPError) as err:
        # This message needs to be useful to an administrator because
        # it will be shown in the Repeat Records report.
        http_error_msg = (
            'An error was when encountered searching patients: {}. Please check that the server is online. If '
            'this is a new forwarding location, please check the server address in Data Forwarding, check that '
            'the server URL includes the path to the API, and that the password is correct'.format(err)
        )
        raise err.__class__(http_error_msg)


def save_match_ids(case, case_config, patient):
    """
    If we are confident of the patient matched to a case, save
    the patient's identifiers to the case.

    Raises DuplicateCaseMatch if external_id is about to be saved with a
        non-unique value.
    """
    def get_patient_id_type_uuids_values(patient_):
        yield PERSON_UUID_IDENTIFIER_TYPE_ID, patient_['uuid']
        for identifier in patient_['identifiers']:
            yield identifier['identifierType']['uuid'], identifier['identifier']

    case_config_ids = case_config['patient_identifiers']
    case_update = {}
    kwargs = {}
    for id_type_uuid, value in get_patient_id_type_uuids_values(patient):
        if id_type_uuid in case_config_ids:
            case_property = case_config_ids[id_type_uuid]['case_property']
            if case_property == 'external_id':
                check_duplicate_case_match(case, value)
                kwargs['external_id'] = value
            else:
                case_update[case_property] = value
    case_block = CaseBlock(
        case_id=case.get_id,
        create=False,
        update=case_update,
        **kwargs
    )
    submit_case_blocks([case_block.as_text()], case.domain, xmlns=XMLNS_OPENMRS)


def check_duplicate_case_match(case, external_id):

    def get_case_str(case_):
        return (f'<Case case_id="{case_.case_id}", domain="{case_.domain}", '
                f'type="{case_.type}" name="{case_.name}">')

    another_case, error = importer_util.lookup_case(
        importer_util.EXTERNAL_ID,
        external_id,
        case.domain,
        case_type=case.type,
    )
    if another_case:
        case_str = get_case_str(case)
        another_case_str = get_case_str(another_case)
        message = (
            f'Unable to match {case_str} with OpenMRS patient "{external_id}": '
            f'{another_case_str} already exists with external_id="{external_id}".'
        )
    elif error == LookupErrors.MultipleResults:
        case_str = get_case_str(case)
        message = (
            f'Unable to match {case_str} with OpenMRS patient "{external_id}": '
            f'Multiple cases already exist with external_id="{external_id}".'
        )
    else: # error == LookupErrors.NotFound:
        return
    raise DuplicateCaseMatch(message)


def create_patient(requests, info, case_config):

    def get_name():
        return {
            property_: value_source.get_value(info)
            for property_, value_source in case_config.person_preferred_name.items()
            if (
                property_ in NAME_PROPERTIES and
                value_source.check_direction(DIRECTION_EXPORT) and
                value_source.get_value(info)
            )
        }

    def get_address():
        return {
            property_: value_source.get_value(info)
            for property_, value_source in case_config.person_preferred_address.items()
            if (
                property_ in ADDRESS_PROPERTIES and
                value_source.check_direction(DIRECTION_EXPORT) and
                value_source.get_value(info)
            )
        }

    def get_properties():
        return {
            property_: value_source.get_value(info)
            for property_, value_source in case_config.person_properties.items()
            if (
                property_ in PERSON_PROPERTIES and
                value_source.check_direction(DIRECTION_EXPORT) and
                value_source.get_value(info)
            )
        }

    def get_identifiers():
        identifiers = []
        for patient_identifier_type, value_source in case_config.patient_identifiers.items():
            if (
                patient_identifier_type != PERSON_UUID_IDENTIFIER_TYPE_ID and
                value_source.check_direction(DIRECTION_EXPORT)
            ):
                identifier = value_source.get_value(info) or generate_identifier(requests, patient_identifier_type)
                if identifier:
                    identifiers.append({
                        'identifierType': patient_identifier_type,
                        'identifier': identifier
                    })
        return identifiers

    person = {}
    name = get_name()
    if name:
        person['names'] = [name]
    address = get_address()
    if address:
        person['addresses'] = [address]
    properties = get_properties()
    if properties:
        person.update(properties)
    if person:
        patient = {
            'person': person,
        }
        identifiers = get_identifiers()
        if identifiers:
            patient['identifiers'] = identifiers
        response = requests.post(
            '/ws/rest/v1/patient/',
            json=patient,
        )
        if 200 <= response.status_code < 300:
            # response.json() is not the full patient record. We need
            # the patient's identifiers and attributes.
            return get_patient_by_uuid(requests, response.json()['uuid'])


def authenticate_session(requests):
    login_data = {
        'uname': requests.username,
        'pw': requests.password,
        'submit': 'Log In',
        'redirect': '',
        'refererURL': '',
    }
    response = requests.post('/ms/legacyui/loginServlet', login_data, headers={'Accept': 'text/html'})
    if not 200 <= response.status_code < 300:
        raise OpenmrsHtmlUiChanged('Domain "{}": Unexpected OpenMRS login page at "{}".'.format(
            requests.domain_name, response.url
        ))


@quickcache(['requests.domain_name', 'requests.base_url', 'identifier_type'])
def get_identifier_source_id(requests, identifier_type):
    """
    Returns the ID of the identifier source to be used for generating
    values for identifiers of the given type.

    The idgen module doesn't offer an API to list identifier sources.
    This function scrapes /module/idgen/manageIdentifierSources.list
    """
    response = requests.get('/ws/rest/v1/patientidentifiertype/{}'.format(identifier_type))
    identifier_type_name = response.json()['name']

    response = requests.get('/module/idgen/manageIdentifierSources.list', headers={'Accept': 'text/html'})
    if not 200 <= response.status_code < 300:
        raise OpenmrsHtmlUiChanged(
            'Domain "{}": Unexpected response from OpenMRS idgen module at "{}". '
            'Is it installed?'.format(requests.domain_name, response.url)
        )

    tree = html.fromstring(response.content)
    for row in tree.xpath('//table[@id="sourceTable"]/tbody/tr'):
        ident_type, source_type, source_name, actions = row.xpath('td')
        if ident_type.text == identifier_type_name:
            try:
                onclick = actions.xpath('button')[1].attrib['onclick']
            except (AttributeError, IndexError, KeyError):
                raise OpenmrsHtmlUiChanged(
                    'Domain "{}": Unexpected page format at "{}".'.format(requests.domain_name, response.url)
                )
            match = re.match(r"document\.location\.href='viewIdentifierSource\.form\?source=(\d+)';", onclick)
            if not match:
                raise OpenmrsHtmlUiChanged(
                    'Domain "{}": Unexpected "onclick" value at "{}".'.format(requests.domain_name, response.url)
                )
            source_id = match.group(1)
            return source_id


def generate_identifier(requests, identifier_type):
    """
    Calls the idgen module's generateIdentifier endpoint

    Identifier source ID is determined from `identifier_type`. If
    `identifier_type` doesn't have an identifier source, return None.
    If the identifier source doesn't return an identifier, return None.
    If anything goes wrong ... return None.

    The idgen module is not a REST API. It does not use API
    authentication. The user has to be logged in using the HTML login
    page, and the resulting authenticated session used for sending
    requests.
    """
    identifier = None
    source_id = None
    with Requests(domain_name=requests.domain_name,
                  base_url=requests.base_url,
                  username=requests.username,
                  password=requests.password,
                  verify=requests.verify) as requests_session:
        authenticate_session(requests_session)
        try:
            source_id = get_identifier_source_id(requests_session, identifier_type)
        except OpenmrsHtmlUiChanged as err:
            requests.notify_exception('Unexpected OpenMRS HTML UI', details=str(err))
        if source_id:
            # Example request: http://www.example.com/openmrs/module/idgen/generateIdentifier.form?source=1
            response = requests_session.get('/module/idgen/generateIdentifier.form', params={'source': source_id})
            try:
                if not (200 <= response.status_code < 300 and response.content):
                    raise OpenmrsException()
                try:
                    # Example response: {"identifiers": ["CHR203007"]}
                    identifier = response.json()['identifiers'][0]
                except (ValueError, IndexError, KeyError):
                    raise OpenmrsException()
            except OpenmrsException:
                requests.notify_exception(
                    'OpenMRS idgen module returned an unexpected response',
                    details=(
                        f'OpenMRS idgen module at "{response.url}" '
                        f'returned an unexpected response {response.status_code}: \r\n'
                        f'{response.content}'
                    )
                )
    return identifier


def find_or_create_patient(requests, domain, info, openmrs_config):
    case = CaseAccessors(domain).get_case(info.case_id)
    patient_finder = PatientFinder.wrap(openmrs_config.case_config.patient_finder)
    if patient_finder is None:
        return
    patients = patient_finder.find_patients(requests, case, openmrs_config.case_config)
    if len(patients) == 1:
        patient, = patients
    elif not patients and patient_finder.create_missing.get_value(info):
        patient = create_patient(requests, info, openmrs_config.case_config)
    else:
        # If PatientFinder can't narrow down the number of candidate
        # patients, don't guess. Just admit that we don't know.
        return None
    try:
        save_match_ids(case, openmrs_config.case_config, patient)
    except DuplicateCaseMatch as err:
        requests.notify_error(str(err), _(
            "Either the same person has more than one CommCare case, or "
            "OpenMRS repeater configuration needs to be modified to match "
            "cases with patients more accurately."
        ))
        return None
    else:
        return patient


def get_patient(requests, domain, info, openmrs_config):
    patient = None
    for id_ in openmrs_config.case_config.match_on_ids:
        identifier = openmrs_config.case_config.patient_identifiers[id_]
        # identifier.case_property must be in info.extra_fields because OpenmrsRepeater put it there
        assert identifier.case_property in info.extra_fields, 'identifier case_property missing from extra_fields'
        patient = get_patient_by_id(requests, id_, info.extra_fields[identifier.case_property])
        if patient:
            break
    else:
        # Definitive IDs did not match a patient in OpenMRS.
        if openmrs_config.case_config.patient_finder:
            # Search for patients based on other case properties
            patient = find_or_create_patient(requests, domain, info, openmrs_config)

    return patient


def get_relevant_case_updates_from_form_json(domain, form_json, case_types, extra_fields,
                                             form_question_values=None):
    result = []
    case_blocks = extract_case_blocks(form_json)
    cases = CaseAccessors(domain).get_cases(
        [case_block['@case_id'] for case_block in case_blocks], ordered=True)
    for case, case_block in zip(cases, case_blocks):
        assert case_block['@case_id'] == case.case_id
        if not case_types or case.type in case_types:
            result.append(CaseTriggerInfo(
                domain=domain,
                case_id=case_block['@case_id'],
                type=case.type,
                name=case.name,
                owner_id=case.owner_id,
                modified_by=case.modified_by,
                updates=dict(
                    list(case_block.get('create', {}).items()) +
                    list(case_block.get('update', {}).items())
                ),
                created='create' in case_block,
                closed='close' in case_block,
                extra_fields={field: case.get_case_property(field) for field in extra_fields},
                form_question_values=form_question_values or {},
            ))
    return result


@quickcache(['requests.base_url'])
def get_unknown_encounter_role(requests):
    """
    Return "Unknown" encounter role for legacy providers with no
    encounter role set
    """
    response_json = requests.get('/ws/rest/v1/encounterrole').json()
    for encounter_role in response_json['results']:
        if encounter_role['display'] == 'Unknown':
            return encounter_role
    raise OpenmrsConfigurationError(
        'The standard "Unknown" EncounterRole was not found on the OpenMRS server at "{}". Please notify the '
        'administrator of that server.'.format(requests.base_url)
    )


@quickcache(['requests.base_url'])
def get_unknown_location_uuid(requests):
    """
    Returns the UUID of Bahmni's "Unknown Location" or None if it
    doesn't exist.
    """
    response_json = requests.get('/ws/rest/v1/location').json()
    for location in response_json['results']:
        if location['display'] == 'Unknown Location':
            return location['uuid']
    return None


def get_patient_identifier_types(requests):
    return requests.get('/ws/rest/v1/patientidentifiertype').json()


def get_person_attribute_types(requests):
    return requests.get('/ws/rest/v1/personattributetype').json()
