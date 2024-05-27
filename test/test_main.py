
import sys
import os
sys.path.append(os.path.join(sys.path[0], '..'))
import json
import main

def load_json(file_name):
    f = open(file_name)
    data = json.load(f)
    return data

def truthy(value):
    return bool(value)

def falsy(value):
    return not bool(value)

def test_validate_handles_api_throttle():
    # Test case : validate handles api throttle
    test_data = load_json("test/sample_response/api-throttle.json")
    qualified_data = main.qualify_data(test_data, testing=True)
    assert falsy(qualified_data)

def test_validate_handles_valid_data():
    # Test case : validate handles valid data
    test_data = load_json("test/sample_response/success.json")
    qualified_data = main.qualify_data(test_data, testing=True)
    assert truthy(qualified_data)

def test_organise_weather_data_with_api_throttle():
    # Test case : organise weather data with api throttle
    test_data = load_json("test/sample_response/api-throttle.json")
    try:
        main.organise_weather_data(test_data, testing=True)
        assert False
    except KeyError:
        assert True

def test_organise_weather_data_with_valid_data():
    # Test case : organise weather data with valid data
    test_data = load_json("test/sample_response/success.json")
    organised_data = main.organise_weather_data(test_data, testing=True)
    assert len(organised_data) > 0
