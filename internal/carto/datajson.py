import math

import shapely
from utils import file_utils, geojson_utils


class CartoJson:
    """
    A class for processing and normalizing GeoJSON data.

    This class handles scaling, translation, and label positioning for GeoJSON features,
    making it easier to work with frontend.
    """

    def __init__(self, json_data: dict):
        """
        Initialize the CartoJson object with GeoJSON data.

        Args:
            json_data (dict): The GeoJSON data containing features and optional dividers
        """
        #: GeoJSON data
        self.json_data = json_data
        #: Geometries created from GeoJSON data for processing
        self.geometries = [
            shapely.geometry.shape(feature["geometry"])
            for feature in json_data["features"]
        ]
        #: Geometries information including bounding box, centriod, and total area of geojson.
        self.geoms_info = geojson_utils.get_geoms_info(self.geometries)

    def postprocess(
        self,
        target_area: float | None = None,
        target_centroid: dict[str, float] | None = None,
    ) -> dict:
        """
        Post-process the GeoJSON data by normalizing scale and adding labels.

        This method performs the complete post-processing workflow:
        1. Normalizes scale and position based on target parameters
        2. Adds representative point labels to each feature
        3. Fixes dividers format if present

        Args:
            target_area (float, optional): Target area for scaling normalization
            target_centroid (dict, optional): Target centroid with 'x' and 'y' keys

        Returns:
            dict: The processed GeoJSON data
        """
        # Normalize scale and position if targets are provided
        self._normalize_scale(target_area, target_centroid)

        # Add label positions to features
        self._add_label_positions()

        # Fix dividers format
        self._fix_dividers_format()

        return self.json_data

    def _normalize_scale(
        self,
        target_area: float | None = None,
        target_centroid: dict[str, float] | None = None,
    ) -> None:
        """
        Scale and translate geometries to match target area and centroid.

        Args:
            target_area (float, optional): Desired total area for all geometries
            target_centroid (dict, optional): Desired centroid position with 'x' and 'y' keys
        """
        # Skip normalization if no targets provided
        if not target_area or not target_centroid:
            return

        # Calculate transformation parameters
        scale_factor = math.sqrt(target_area / self.geoms_info["area"])
        origin_x = self.geoms_info["centroid"]["x"]
        origin_y = self.geoms_info["centroid"]["y"]
        diff_x = target_centroid["x"] - origin_x
        diff_y = target_centroid["y"] - origin_y

        # Transform each feature geometry
        self._transform_features(scale_factor, origin_x, origin_y, diff_x, diff_y)

        # Transform dividers if present
        self._transform_dividers(scale_factor, origin_x, origin_y, diff_x, diff_y)

        # Update bounding box and geoms_info["bbox"]
        self._update_bbox(scale_factor, origin_x, origin_y, diff_x, diff_y)

        # Update other geoms_info
        self.geoms_info["area"] = target_area
        self.geoms_info["centroid"]["x"] = target_centroid["x"]
        self.geoms_info["centroid"]["y"] = target_centroid["y"]

    def _transform_features(
        self,
        scale_factor: float,
        origin_x: float,
        origin_y: float,
        diff_x: float,
        diff_y: float,
    ) -> None:
        """
        Apply scaling and translation transformations to all features.

        Args:
            scale_factor (float): Factor to scale geometries
            origin_x, origin_y (float): Origin point for scaling
            diff_x, diff_y (float): Translation offsets
        """
        for index, feature in enumerate(self.json_data["features"]):
            # Scale geometry around origin point
            self.geometries[index] = shapely.affinity.scale(
                self.geometries[index],
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(origin_x, origin_y),
            )

            # Translate geometry to target position
            self.geometries[index] = shapely.affinity.translate(
                self.geometries[index],
                xoff=diff_x,
                yoff=diff_y,
            )

            # Update the GeoJSON geometry with transformed coordinates
            feature["geometry"] = shapely.geometry.mapping(self.geometries[index])

    def _transform_dividers(
        self,
        scale_factor: float,
        origin_x: float,
        origin_y: float,
        diff_x: float,
        diff_y: float,
    ) -> None:
        """
        Apply transformations to dividers if they exist in the data.

        Args:
            scale_factor (float): Factor to scale geometries
            origin_x, origin_y (float): Origin point for scaling
            diff_x, diff_y (float): Translation offsets
        """
        if "dividers" not in self.json_data:
            return

        # Transform dividers geometry
        dividers_geom = shapely.geometry.shape(self.json_data["dividers"]["geometry"])

        # Scale around origin point
        adjusted_dividers = shapely.affinity.scale(
            dividers_geom,
            xfact=scale_factor,
            yfact=scale_factor,
            origin=(origin_x, origin_y),
        )

        # Translate to target position
        adjusted_dividers = shapely.affinity.translate(
            adjusted_dividers,
            xoff=diff_x,
            yoff=diff_y,
        )

        # Update dividers geometry in JSON data
        self.json_data["dividers"]["geometry"] = shapely.geometry.mapping(
            adjusted_dividers
        )

    def _update_bbox(
        self,
        scale_factor: float,
        origin_x: float,
        origin_y: float,
        diff_x: float,
        diff_y: float,
    ):
        """
        Update the bounding box after transformations.

        Args:
            scale_factor (float): Applied scale factor
            origin_x, origin_y (float): Origin point used for scaling
            diff_x, diff_y (float): Applied translation offsets
        """
        # Transform each corner of the bounding box
        # Format: [min_x, min_y, max_x, max_y]
        self.geoms_info["bbox"][0] = (
            origin_x + (self.geoms_info["bbox"][0] - origin_x) * scale_factor
        ) + diff_x
        self.geoms_info["bbox"][1] = (
            origin_y + (self.geoms_info["bbox"][1] - origin_y) * scale_factor
        ) + diff_y
        self.geoms_info["bbox"][2] = (
            origin_x + (self.geoms_info["bbox"][2] - origin_x) * scale_factor
        ) + diff_x
        self.geoms_info["bbox"][3] = (
            origin_y + (self.geoms_info["bbox"][3] - origin_y) * scale_factor
        ) + diff_y

        self.json_data["bbox"] = self.geoms_info["bbox"]

    def _add_label_positions(self):
        """
        Add representative point coordinates to each feature for label placement.

        This method calculates a suitable point within each geometry where
        labels can be positioned, typically used for map labeling.
        """
        for index, feature in enumerate(self.json_data["features"]):
            # Get a representative point that's guaranteed to be inside the geometry
            point = self.geometries[index].representative_point()

            # Add label position to feature properties
            if "properties" not in feature:
                feature["properties"] = {}

            feature["properties"]["label"] = {"x": point.x, "y": point.y}

    def _fix_dividers_format(self):
        """
        Ensure dividers are in the correct array format.

        This method wraps single divider objects in an array for consistency
        with expected data structure.
        """
        if "dividers" in self.json_data and not isinstance(
            self.json_data["dividers"], list
        ):
            self.json_data["dividers"] = [self.json_data["dividers"]]

    def save(self, project_path: str, filename: str, is_projected: bool = False) -> str:
        """
        Save the processed GeoJSON data to a file.

        Args:
            project_path: Folder path where the GeoJson should be saved
            filename: File name of the GeoJson
            is_projected (bool): Whether this GeoJson is already projected

        Returns:
            str: File path where the GeoJson is saved
        """
        import json

        filepath = file_utils.get_safepath(project_path, filename)

        self.json_data = geojson_utils.add_attributes(
            self.json_data, is_projected=is_projected
        )

        with open(filepath, "w") as f:
            json.dump(self.json_data, f)

        return filepath
