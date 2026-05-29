import json
import warnings

from carto.dataframe import CartoDataFrame


# Successfully reads valid GeoJSON file and creates CartoDataFrame instance
def test_read_file(test_data_dir):
    geojson_file = test_data_dir / "geojson_test.geojson"
    carto_df = CartoDataFrame.read_file(str(geojson_file))
    assert isinstance(carto_df, CartoDataFrame)

    expected_extra_attributes = {
        "crs": {"properties": {"name": "EPSG:cartesian"}},
    }

    assert isinstance(carto_df.extra_attributes, dict)
    assert carto_df.extra_attributes == expected_extra_attributes  # type: ignore[reportGeneralTypeIssues]

    carto_json = json.loads(carto_df.to_json())
    assert "bbox" not in carto_json
    assert carto_df.is_projected
    assert not carto_df.is_world


def test_crs(test_data_dir):
    geojson_file = test_data_dir / "usa_by_state_since_1959.geojson"
    carto_df = CartoDataFrame.read_file(str(geojson_file))
    assert carto_df.crs == "EPSG:4326"

    carto_df.to_crs("EPSG:6933", inplace=True)
    assert carto_df.crs == "EPSG:6933"

    # carto_df2 = CartoDataFrame.read_file("tests/data/usa_by_state_since_1959_EPSG6933.geojson")
    # assert carto_df2.crs == "EPSG:6933"


def test_clean_properties_with_existing_region_column(mocker):
    json_data = {
        "Region": ["B", "A"],
        "geometry": [None, None],
        "Geographic Area (sq. km)": [100, 200],
        "other": ["1", "2"],
    }
    carto_df = CartoDataFrame(json_data)
    carto_df.clean_properties("Region")
    assert "Region" in carto_df.columns
    assert "other" not in carto_df.columns
    assert list(carto_df["Region"]) == ["B", "A"]


def test_clean_properties_with_other_region_column(test_data_dir):
    geojson_file = test_data_dir / "geojson_test.geojson"
    carto_df = CartoDataFrame.read_file(str(geojson_file))
    carto_df.clean_properties("prop_unique")
    carto_json = carto_df.to_json_obj()
    # carto_df.to_carto_file("tests/data/geojson_out.geojson")

    assert "Region" in carto_json["features"][0]["properties"]
    assert "99" == carto_json["features"][0]["properties"]["Region"]
    assert "prop_non_unique" not in carto_json["features"][0]["properties"]


def test_invalid_geometry_auto_repair(test_data_dir):
    """Test that invalid (self-intersecting) geometries are automatically repaired with a warning."""
    geojson_file = test_data_dir / "invalid_geometry.geojson"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        carto_df = CartoDataFrame.read_file(str(geojson_file))

        # Should have emitted a warning about invalid geometry
        geometry_warnings = [
            x for x in w if "Invalid geometry detected" in str(x.message)
        ]
        assert len(geometry_warnings) == 1
        assert "1 geometry(ies)" in str(geometry_warnings[0].message)
        assert "automatically repaired" in str(geometry_warnings[0].message)

    # The resulting dataframe should have valid, simple geometries
    assert isinstance(carto_df, CartoDataFrame)
    assert carto_df.is_simple.all()
    assert len(carto_df) == 2


def test_valid_geometry_no_warning(test_data_dir):
    """Test that valid geometries don't trigger any geometry repair warning."""
    geojson_file = test_data_dir / "usa_by_state_since_1959.geojson"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        carto_df = CartoDataFrame.read_file(str(geojson_file))

        geometry_warnings = [
            x for x in w if "Invalid geometry detected" in str(x.message)
        ]
        assert len(geometry_warnings) == 0

    assert isinstance(carto_df, CartoDataFrame)
