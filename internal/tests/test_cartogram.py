from carto import boundary, project


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
    vis_types = {"cartogram": ["Population (people)"]}
    csv_string = "Region,RegionLabel,Color,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000"
    expected_csv_string = "Region,RegionLabel,ColorGroup,Geographic Area (sq. km)\nRegion1,R1,,1000\nRegion2,R2,,2000\n"

    formatted_csv, data_cols, prefered_names_dict = project.process_data(
        csv_string, vis_types
    )
    assert formatted_csv == expected_csv_string
    assert len(data_cols) == 0


def test_process_data_with_color_inset(mocker):
    vis_types = {"cartogram": ["Population (people)"]}
    csv_string = "Region,RegionLabel,Color,Inset,Population (people)\nRegion1,R1,#fff,C,1000\nRegion2,R2,,C,2000"
    expected_csv_string = "Region,RegionLabel,Color,ColorGroup,Inset,Population (people)\nRegion1,R1,#fff,,C,1000\nRegion2,R2,,,C,2000\n"
    formatted_csv, data_cols, prefered_names_dict = project.process_data(
        csv_string, vis_types
    )

    assert formatted_csv == expected_csv_string
    assert data_cols == [{"name": "Population", "column_name": "Population (people)"}]
