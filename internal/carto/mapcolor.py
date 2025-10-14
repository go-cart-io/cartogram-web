import warnings

import gcol
from geopandas import GeoDataFrame
from libpysal.weights import Rook


def assign_colors(gdf: GeoDataFrame):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Fix geometries (avoid topology errors)
        gdf = gdf.set_geometry(gdf.geometry.buffer(0))

        # Build adjacency
        weight = Rook.from_dataframe(gdf, use_index=True)
        graph = weight.to_networkx()  # type: ignore

        # Run GCol coloring
        colors = gcol.equitable_node_k_coloring(graph, 6)  # type: ignore

        return gdf.index.map(colors)
