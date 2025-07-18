import json
import warnings
from typing import Any

import geopandas as gpd
import util


class CartoDataFrame(gpd.GeoDataFrame):
    """A subclass of GeoDataFrame that preserves extra attributes when reading and writing GeoJSON."""

    # Make sure Pandas doesn't try to treat `extra_attributes` as a DataFrame column
    _metadata = ["extra_attributes"]
    is_projected = False
    is_world = False

    def __new__(cls, *args, extra_attributes={}, **kwargs):
        obj = object.__new__(cls)
        return obj

    def __init__(self, *args, extra_attributes={}, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "extra_attributes", extra_attributes or {})

        self.is_projected = (
            extra_attributes.get("crs", {}).get("properties", {}).get("name")
            == "EPSG:cartesian"
        )
        self.is_world = extra_attributes.get("extent") == "world"

    def __setattr__(self, attr, val):
        """Ensure extra attributes are stored properly without interfering with the DataFrame structure."""
        if attr in self._metadata:
            object.__setattr__(self, attr, val)  # Store metadata normally
        else:
            super().__setattr__(
                attr, val
            )  # Let GeoDataFrame handle standard attributes

    # Override Filtering to Preserve Subclass
    def __getitem__(self, key: Any) -> Any:
        """Ensure filtering returns a CartoDataFrame when appropriate."""
        result = super().__getitem__(key)
        if isinstance(result, gpd.GeoDataFrame):
            return CartoDataFrame(result, extra_attributes=self.extra_attributes)
        return result

    @classmethod
    def read_file(cls, filepath):
        filepath = util.get_safepath(filepath)
        extra_attributes = {}

        # Reads a GeoJSON file and preserves extra attributes.
        # If fail, just try again with GeoPandas only
        if filepath.lower().endswith(".json") or filepath.lower().endswith(".geojson"):
            encodings = ["utf-8", "utf-16", "latin-1", "iso-8859-1", "windows-1252"]
            try:
                for encoding in encodings:
                    with open(filepath, "r", encoding=encoding) as f:
                        data = json.load(f)
                        extra_attributes = {
                            key: value
                            for key, value in data.items()
                            if key != "features"
                        }
                        break
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass

        gdf = gpd.read_file(filepath)
        return cls(gdf, extra_attributes=extra_attributes)

    def to_crs(self, *args, force: bool = False, **kwargs) -> Any:
        """
        Overrides GeoDataFrame's to_crs method.
        If the GeoDataFrame is already projected, prints a warning before reprojecting.
        """
        if self.is_projected and not force:
            warnings.warn(
                "The file is already projected. This reprojection may be incorrect.",
                UserWarning,
            )
        if "crs" in self.extra_attributes:
            del self.extra_attributes["crs"]

        result = super().to_crs(*args, **kwargs)
        if result is None:
            return None

        return CartoDataFrame(result, extra_attributes=self.extra_attributes)

    def to_json(self, *args, **kwargs):
        return json.dumps(self.to_json_obj(*args, **kwargs))

    def to_json_obj(self, *args, **kwargs):
        return {
            "type": "FeatureCollection",
            **self.extra_attributes,
            "features": json.loads(super().to_json(*args, **kwargs))["features"],
        }

    def to_carto_file(self, filepath):
        output_data = self.to_json_obj()
        with open(util.get_safepath(filepath), "w") as f:
            json.dump(output_data, f)
        return output_data

    def reset_index(self, *args, **kwargs) -> Any:
        """Ensure reset_index returns a CartoDataFrame."""
        result = super().reset_index(*args, **kwargs)
        if result is None:
            return None

        return CartoDataFrame(result, extra_attributes=self.extra_attributes)

    def clean_properties(
        self,
        region_col,
        base_columns=["Region", "label", "cartogram_id", "geometry"],
        prefered_names_dict={},
    ):
        """
        Cleans the GeoDataFrame by:
        - Renaming `region_col` to 'Region'
        - Dropping existing 'Region' column if necessary
        - Keeping only relevant columns
        """
        # Rename or replace 'Region' column
        if region_col != "Region":
            if "Region" in self.columns:
                self.drop(columns=["Region"], inplace=True)
            self.rename(columns={region_col: "Region"}, inplace=True)

        if prefered_names_dict != {}:
            self["Region"] = self["Region"].apply(
                lambda x: prefered_names_dict.get(x, x)
            )

        # Identify columns to keep
        area_columns = [
            col for col in self.columns if col.startswith("Geographic Area")
        ]
        columns_to_keep = base_columns + area_columns
        existing_columns = [col for col in columns_to_keep if col in self.columns]

        # Filter columns
        self.drop(
            columns=[col for col in self.columns if col not in existing_columns],
            inplace=True,
        )

        if "label" in self.columns:
            self["label"] = self["label"].apply(json.loads)
