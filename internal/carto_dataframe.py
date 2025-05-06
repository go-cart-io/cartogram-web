import json
import warnings

import geopandas as gpd
import util


class CartoDataFrame(gpd.GeoDataFrame):
    """A subclass of GeoDataFrame that preserves extra attributes when reading and writing GeoJSON."""

    # Make sure Pandas doesn't try to treat `extra_attributes` as a DataFrame column
    _metadata = ["extra_attributes"]
    is_projected = False
    is_world = False

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
    def __getitem__(self, key):
        """Ensure filtering returns a CartoDataFrame."""
        result = super().__getitem__(key)
        if isinstance(result, gpd.GeoDataFrame):
            return CartoDataFrame(result, extra_attributes=self.extra_attributes)
        return result

    @classmethod
    def read_file(cls, filepath):
        filepath = util.get_safepath(filepath)

        """Reads a GeoJSON file and preserves extra attributes."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        extra_attributes = {
            key: value for key, value in data.items() if key != "features"
        }
        gdf = gpd.read_file(filepath)
        return cls(gdf, extra_attributes=extra_attributes)

    def to_crs(self, crs=None, epsg=None, inplace=False):
        """
        Overrides GeoDataFrame's to_crs method.
        If the GeoDataFrame is already projected, prints a warning before reprojecting.
        """
        if self.is_projected:
            warnings.warn(
                "The file is already projected. This reprojection may be incorrect.",
                UserWarning,
            )
        if "crs" in self.extra_attributes:
            del self.extra_attributes["crs"]

        return super().to_crs(crs=crs, epsg=epsg, inplace=inplace)

    def to_json(self, *args, **kwargs):
        return {
            **self.extra_attributes,
            "features": json.loads(super().to_json(*args, **kwargs))["features"],
        }

    def to_carto_file(self, filepath):
        output_data = self.to_json()
        with open(util.get_safepath(filepath), "w") as f:
            json.dump(output_data, f)
        return output_data

    def reset_index(self, *args, **kwargs):
        """Ensure reset_index returns a CartoDataFrame."""
        result = super().reset_index(*args, **kwargs)
        return CartoDataFrame(result, extra_attributes=self.extra_attributes)

    def clean_and_sort(
        self,
        region_col,
        base_columns=["Region", "label", "cartogram_id", "geometry"],
        prefered_names_dict={},
    ):
        """
        Cleans and sorts the GeoDataFrame by:
        - Renaming `region_col` to 'Region'
        - Dropping existing 'Region' column if necessary
        - Keeping only relevant columns
        - Sorting by 'Region'
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
        columns_to_keep = ["Region", "label", "cartogram_id", "geometry"] + area_columns
        existing_columns = [col for col in columns_to_keep if col in self.columns]

        # Filter columns
        self.drop(
            columns=[col for col in self.columns if col not in existing_columns],
            inplace=True,
        )

        # Sort by 'Region'
        self.sort_values(by="Region", inplace=True)

        if "label" in self.columns:
            self["label"] = self["label"].apply(json.loads)
