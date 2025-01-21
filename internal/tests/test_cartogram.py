import json
import cartogram
import uuid

def test_preprocess():
    result = cartogram.preprocess('tests/data/geojson_test.geojson')
    assert 'geojson' in result
    
    # Should only allow Polygon and MultiPolygon
    geojson = json.loads(result['geojson'])
    assert len(geojson['features']) == 2

    # Should identify property with unique values
    assert 'unique' in result
    assert result['unique'] == ['prop_unique']

def test_process_data_with_no_color_no_inset(mocker):
    csv_string = "Region,RegionLabel,Color,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000"
    geojson_file = "path/to/geojson/file"

    mocker.patch('geopandas.read_file', return_value=mocker.Mock(to_crs=lambda x: mocker.Mock()))
    mocker.patch('mapclassify.greedy', return_value=[1, 2])

    formatted_csv, datasets, is_area_as_base = cartogram.process_data(csv_string, geojson_file)

    assert formatted_csv == "Region,RegionLabel,ColorGroup,Geographic Area (sq. km)\nRegion1,R1,1,1000\nRegion2,R2,2,2000\n"
    assert len(datasets) == 0
    assert is_area_as_base is True

def test_process_data_with_color_inset(mocker):
    csv_string = "Region,RegionLabel,Color,Inset,Population (people)\nRegion1,R1,#fff,C,1000\nRegion2,R2,,C,2000"
    geojson_file = "path/to/geojson/file"

    mocker.patch('geopandas.read_file', return_value=mocker.Mock(to_crs=lambda x: mocker.Mock()))
    mocker.patch('mapclassify.greedy', return_value=[1, 2])

    formatted_csv, datasets, is_area_as_base = cartogram.process_data(csv_string, geojson_file)

    assert formatted_csv == "Region,RegionLabel,Color,ColorGroup,Inset,Population (people)\nRegion1,R1,#fff,1,C,1000\nRegion2,R2,,2,C,2000\n"
    assert datasets == [{'label': 'Population', 'datastring': 'Region,Data,Color,Inset\nRegion1,1000,#fff,C\nRegion2,2000,,C\n'}]
    assert is_area_as_base is False

def test_local_function_equal_area():
    lambda_event = {
        'gen_file': 'tests/data/geojson_test.geojson',
        'key': str(uuid.uuid4()),
        'flags': '--output_equal_area',
        'world': False
    }
    i = 0
    data_length = 1
    print_progress = True

    result = cartogram.local_function(lambda_event, i, data_length, print_progress)
    assert 'stdout' in result
    assert 'error_msg' in result
    # print(result)
