import cartogram


def test_preprocess():
    result = cartogram.preprocess("tests/data/geojson_test.geojson")
    assert "geojson" in result

    # Should only allow Polygon and MultiPolygon
    geojson = result["geojson"]
    assert len(geojson["features"]) == 2

    # Should identify property with unique values
    assert "unique" in result
    assert result["unique"] == ["prop_unique"]


def test_process_data_with_no_inset(mocker):
    csv_string = "Region,RegionLabel,Color,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000"
    formatted_csv, datasets, is_area_as_base, prefered_names_dict = (
        cartogram.process_data(csv_string)
    )

    assert (
        formatted_csv
        == "Region,RegionLabel,ColorGroup,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000\n"
    )
    assert len(datasets) == 0
    assert is_area_as_base is True


def test_process_data_with_color_inset(mocker):
    csv_string = "Region,RegionLabel,Color,Inset,Population (people)\nRegion1,R1,#fff,C,1000\nRegion2,R2,,C,2000"
    formatted_csv, datasets, is_area_as_base, prefered_names_dict = (
        cartogram.process_data(csv_string)
    )

    assert (
        formatted_csv
        == "Region,RegionLabel,Color,ColorGroup,Inset,Population (people)\nRegion1,R1,#fff,,C,1000\nRegion2,R2,,,C,2000\n"
    )
    assert datasets == [
        {
            "label": "Population",
            "datastring": "Region,Data,Color,Inset\nRegion1,1000,#fff,C\nRegion2,2000,,C\n",
        }
    ]
    assert is_area_as_base is False
