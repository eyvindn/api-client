import mock
import numpy as np

from api.client import lib
import platform
from pkg_resources import get_distribution

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'
PYTHON_VERSION = platform.python_version()
API_CLIENT_VERSION = get_distribution('gro').version

LOOKUP_MAP = {
    'metrics': {},
    'items': {},
    'regions': {
        '1': {'id': 1, 'name': 'region 1', 'contains': [], 'belongsTo': [3], 'historical': True},
        '2': {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False},
        '3': {'id': 3, 'name': 'parent', 'contains': [1, 2], 'belongsTo': [4], 'historical': False},
        '4': {'id': 4, 'name': 'ancestor', 'contains': [3], 'belongsTo': [], 'historical': False}
    },
    'frequencies': {},
    'sources': {},
    'units': {}
}


def initialize_requests_mocker_and_get_mock_data(mock_requests_get, mock_data={
    'data': [
        {'name': 'obj1'},
        {'name': 'obj2'},
        {'name': 'obj3'}
    ]}
):
    mock_requests_get.return_value.json.return_value = mock_data
    mock_requests_get.return_value.status_code = 200
    return mock_data


@mock.patch('requests.get')
def test_get_available(mock_requests_get):
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    # Test data
    entity_types = ['items', 'metrics', 'regions']

    for ent_type in entity_types:
        assert lib.get_available(MOCK_TOKEN, MOCK_HOST, ent_type) == mock_data['data']


@mock.patch('requests.get')
def test_list_available(mock_requests_get):
    # Tests the base functionality
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    entities = {'metricId': '123', 'itemId': '456', 'regionId': '789'}

    assert lib.list_available(MOCK_TOKEN, MOCK_HOST, entities) == mock_data['data']


@mock.patch('requests.get')
def test_list_available_snake_to_camel(mock_requests_get):
    # Tests that the camel-ing fix is working properly.
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)
    entities = {'metric_id': '123', 'item_id': '456', 'regionId': '789'}
    assert lib.list_available(MOCK_TOKEN, MOCK_HOST, entities) == mock_data['data']


@mock.patch('requests.get')
def test_single_lookup(mock_requests_get):
    api_response = {'data': {'12345': {'id': 12345, 'name': 'Test', 'contains': []}}}
    initialize_requests_mocker_and_get_mock_data(mock_requests_get, api_response)
    expected_return = {'id': 12345, 'name': 'Test', 'contains': []}
    assert lib.lookup(MOCK_TOKEN, MOCK_HOST, 'items', 12345) == expected_return


@mock.patch('requests.get')
def test_multiple_lookups(mock_requests_get):
    api_response = {
        'data': {
            '12345': {'id': 12345, 'name': 'Vegetables', 'contains': [67890], 'belongsTo': []},
            '67890': {'id': 67890, 'name': 'Eggplant', 'contains': [], 'belongsTo': [12345]}
        }
    }
    initialize_requests_mocker_and_get_mock_data(mock_requests_get, api_response)
    expected_return = {
        '12345': {'id': 12345, 'name': 'Vegetables', 'contains': [67890], 'belongsTo': []},
        '67890': {'id': 67890, 'name': 'Eggplant', 'contains': [], 'belongsTo': [12345]}
    }
    assert lib.lookup(MOCK_TOKEN, MOCK_HOST, 'items', [12345, 67890]) == expected_return


@mock.patch('requests.get')
def test_lookup_with_numpy(mock_requests_get):
    api_response = {
        'data': {
            '12345': {'id': 12345, 'name': 'Vegetables', 'contains': [67890], 'belongsTo': []},
            '67890': {'id': 67890, 'name': 'Eggplant', 'contains': [], 'belongsTo': [12345]}
        }
    }
    initialize_requests_mocker_and_get_mock_data(mock_requests_get, api_response)
    expected_return = {
        '12345': {'id': 12345, 'name': 'Vegetables', 'contains': [67890], 'belongsTo': []},
        '67890': {'id': 67890, 'name': 'Eggplant', 'contains': [], 'belongsTo': [12345]}
    }
    assert lib.lookup(MOCK_TOKEN, MOCK_HOST, 'items', np.array([12345, 67890])) == expected_return

    assert lib.lookup(MOCK_TOKEN, MOCK_HOST, 'items',
                      np.array([12345])[0]) == expected_return['12345']


@mock.patch('requests.get')
def test_get_data_series(mock_requests_get):
    # Test general case
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)
    selection_dict = {'item_id': 123, 'metric_id': 456, 'region_id': 789,
                      'partner_region_id': 161718, 'frequency_id': 101112, 'source_id': 12}

    assert lib.get_data_series(MOCK_TOKEN, MOCK_HOST, **selection_dict) == mock_data['data']


@mock.patch('requests.get')
def test_get_data_points(mock_requests_get):
    list_of_series_format_data = [{
        'series': {},
        'data': [['2000-01-01', '2000-12-31', 1]]
    }]
    single_series_format_data = [{
        'start_date': '2000-01-01',
        'end_date': '2000-12-31',
        'value': 1,
        'unit_id': None,
        'input_unit_id': None,
        'input_unit_scale': 1,
        'reporting_date': None,
        'metric_id': None,
        'item_id': None,
        'region_id': None,
        'partner_region_id': 0,
        'frequency_id': None,
        # 'source_id': None, TODO: add source to output
    }]
    initialize_requests_mocker_and_get_mock_data(mock_requests_get,
                                                 mock_data=list_of_series_format_data)

    # Test data
    selection_dict = {'item_id': 123, 'metric_id': 456, 'region_id': 789,
                      'frequency_id': 101112, 'source_id': 131415, 'partner_region_id': 161718}

    assert lib.get_data_points(MOCK_TOKEN, MOCK_HOST, **selection_dict) == single_series_format_data


@mock.patch('requests.get')
def test_search(mock_requests_get):
    mock_data = ['obj1', 'obj2', 'obj3']
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get, mock_data=mock_data)

    assert lib.search(MOCK_TOKEN, MOCK_HOST, 'items', 'test123') == mock_data


@mock.patch('api.client.lib.lookup')
@mock.patch('api.client.lib.search')
def test_search_and_lookup(search_mocked, lookup_mocked):
    # Set up
    # mock return values
    search_mocked.return_value = [{'id': 1}, {'id': 2}]
    lookup_mocked.side_effect = lookup_mock
    search_and_lookup_result = list(lib.search_and_lookup(MOCK_TOKEN, MOCK_HOST,
                                                          'regions', 'test123'))

    assert search_and_lookup_result == [
        LOOKUP_MAP['regions']['1'],
        LOOKUP_MAP['regions']['2']
    ]


@mock.patch('api.client.lib.lookup')
@mock.patch('requests.get')
def test_lookup_belongs(mock_requests_get, lookup_mocked):
    mock_requests_get.return_value.json.return_value = {'data': {'1': [3]}}
    mock_requests_get.return_value.status_code = 200
    lookup_mocked.side_effect = lookup_mock

    lookup_belongs_result = list(lib.lookup_belongs(MOCK_TOKEN, MOCK_HOST, 'regions', 1))

    assert lookup_belongs_result == [LOOKUP_MAP['regions']['3']]


@mock.patch('requests.get')
def test_get_source_ranking(mock_requests_get):
    mock_return = [60, 14, 2, 1]
    mock_requests_get.return_value.json.return_value = mock_return
    mock_requests_get.return_value.status_code = 200

    query_parameters = {'item_id': 1, 'metric_id': 2, 'region_id': 3, 'frequency_id': 4}

    ranked_sources_list = lib.get_source_ranking(MOCK_TOKEN, MOCK_HOST, query_parameters)
    assert len(ranked_sources_list) == 4


@mock.patch('requests.get')
def test_rank_series_by_source(mock_requests_get):
    # for each series selection, mock ranking of 3 source ids
    mock_return = [11, 22, 33]
    mock_requests_get.return_value.json.return_value = mock_return
    mock_requests_get.return_value.status_code = 200

    a = {'region_id': 13474, 'abc': 123, 'def': 123, 'ghe': 123, 'fij': 123,
         'item_id': 3457, 'metric_id': 2540047,
         'source_id': 123, 'source_name': 'dontcare'}
    a.pop('abc')
    a.pop('def')
    a.pop('ghe')
    a.pop('fij')

    b = {'item_id': 1457, 'region_id': 13474, 'metric_id': 2540047}
    c = list(lib.rank_series_by_source(MOCK_TOKEN, MOCK_HOST, [a, b]))

    assert(len(c) == 6)
    for x in c:
        assert 'source_name' not in x
    assert mock_return + mock_return == [x['source_id'] for x in c]


def lookup_mock(MOCK_TOKEN, MOCK_HOST, entity_type, entity_ids):
    if isinstance(entity_ids, int):
        return LOOKUP_MAP[entity_type][str(entity_ids)]
    if isinstance(entity_ids, list):
        return {str(entity_id): LOOKUP_MAP[entity_type][str(entity_id)]
                for entity_id in entity_ids}


@mock.patch('api.client.lib.lookup')
@mock.patch('requests.get')
def test_descendant_regions(mock_requests_get, lookup_mocked):
    mock_requests_get.return_value.json.return_value = {'data': {'3': [1, 2]}}
    mock_requests_get.return_value.status_code = 200
    lookup_mocked.side_effect = lookup_mock

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3) == [
        {'id': 1, 'name': 'region 1', 'contains': [], 'belongsTo': [3], 'historical': True},
        {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3, include_details=True) == [
        {'id': 1, 'name': 'region 1', 'contains': [], 'belongsTo': [3], 'historical': True},
        {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3, include_details=False) == [
        {'id': 1}, {'id': 2}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3, include_historical=True) == [
        {'id': 1, 'name': 'region 1', 'contains': [], 'belongsTo': [3], 'historical': True},
        {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3, include_historical=False) == [
        {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3,
                                      include_historical=True, include_details=True) == [
        {'id': 1, 'name': 'region 1', 'contains': [], 'belongsTo': [3], 'historical': True},
        {'id': 2, 'name': 'region 2', 'contains': [], 'belongsTo': [3], 'historical': False}
    ]

    assert lib.get_descendant_regions(MOCK_TOKEN, MOCK_HOST, 3, include_historical=False,
                                      include_details=False) == [{'id': 2}]


@mock.patch('requests.get')
def test_get_top(mock_requests_get):
    mock_response = [
        {'itemId': 274, 'value': 13175206696, 'unitId': 14},
        {'itemId': 574, 'value': 13175206878, 'unitId': 14},
        {'itemId': 7193, 'value': 13175206343, 'unitId': 14}
    ]
    mock_requests_get.return_value.json.return_value = mock_response
    mock_requests_get.return_value.status_code = 200
    assert lib.get_top(MOCK_TOKEN, MOCK_HOST, 'items', metric_id=14) == mock_response
    assert lib.get_top(MOCK_TOKEN, MOCK_HOST, 'items', num_results=3, metric_id=14) == mock_response
