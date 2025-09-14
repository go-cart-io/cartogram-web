from unittest.mock import mock_open, patch

from carto import boundary, datacsv


def test_preprocess(test_data_dir):
    geojson_file = test_data_dir / "geojson_test.geojson"
    result = boundary.preprocess(str(geojson_file))
    assert "geojson" in result

    # Should only allow Polygon and MultiPolygon
    geojson = result["geojson"]
    assert len(geojson["features"]) == 2

    # Should identify property with unique values
    assert "unique" in result
    assert result["unique"] == ["prop_unique"]


def test_process_data_with_no_inset(mocker):
    vis_types = {}
    csv_string = "Region,RegionLabel,Color,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000"
    expected_csv_string = "Region,RegionLabel,ColorGroup,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000\n"

    mocked_open = mock_open()
    with patch("builtins.open", mocked_open):
        map_regions_dict, data_names = datacsv.process_data(
            csv_string, vis_types, "tmp/test.txt"
        )

        mocked_open.assert_called_once_with("tmp/test.txt", "w")
        mocked_open().write.assert_called_once_with(expected_csv_string)

        assert map_regions_dict == {}
        assert data_names == {}


def test_process_data_with_color_inset(mocker):
    vis_types = {"cartogram": ["Population (people)"]}
    csv_string = "Region,RegionLabel,Color,Inset,Population (people)\nRegion1,R1,#fff,C,1000\nRegion2,R2,,C,2000"
    expected_csv_string = "Region,RegionLabel,Color,ColorGroup,Inset,Population (people)\nRegion1,R1,#fff,,C,1000\nRegion2,R2,,,C,2000\n"

    mocked_open = mock_open()
    with patch("builtins.open", mocked_open):
        map_regions_dict, data_names = datacsv.process_data(
            csv_string, vis_types, "tmp/test.txt"
        )

        mocked_open.assert_called_once_with("tmp/test.txt", "w")
        mocked_open().write.assert_called_once_with(expected_csv_string)

        assert map_regions_dict == {}
        assert data_names == {"Population (people)": "Population"}
