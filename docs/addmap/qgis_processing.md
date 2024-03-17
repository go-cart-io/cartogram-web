# Guide to processing maps from GADM using QGIS

- [Step 1: Download your map from GADM](#step-1-download-your-map-from-gadm)
- [Step 2: Process your map in QGIS](#step-2-process-your-map-in-qgis)
  * [Step 2.1: Importing](#step-21-importing)
  * [Step 2.2: Projection](#step-22-projection)
  * [Step 2.3: Simplification](#step-23-simplification)
  * [Step 2.4: Exporting](#step-24-exporting)

## Step 1: Download your map from GADM
Vist https://gadm.org. Select "Data", "country", your desired country from the dropdown menu, and "Shapefile". Unzip the Shapefile into your preferred directory.

## Step 2: Process your map in QGIS
You will now process your map in QGIS.

### Step 2.1: Importing
Open QGIS and in the main toolbar, select `Project` > `Open...`, navigate to the directory containing the Shapefiles, and open the `.shp` file.

### Step 2.2: Projection
Note: Be sure to have the GRASS plugin shown on QGIS. To show it, go to Plugins > Manage and install plugins, and tick the box that says GRASS 7

First, we need to create a mapset to process the world map. 
Go to Plugins > GRASS > New mapset, and follow the steps provided. 

- On the window titled "GRASS Database", simply decide where to store your map data
- On the window titled "GRASS Location", create a new location called "World"
- On the window titled "Projection", locate and select the coordinate reference system WGS 84, which can be found by typing "4326" in the filter box
- On the window titled "Default GRASS region", enter the extent coordinates as North: 90, South: -90, East: 180, West: -180
- On the window titled "Mapset", name your mapset

Once you are done creating your mapeset, go to Plugins > GRASS > Open mapset, and select the mapset that you created. A red bounding box should display.
Finally, open your map in QGIS by dragging the GeoJSON file into the QGIS work space. It should display within the bounds of the red bounding box

Now, we must load the data into the GRASS mapset

- In the third toolbox row in QGIS, click the first icon of tools and grass. This opens the GRASS toolbox.
- In the "modules tab", search for "v.in.ogr.qgis."
- In the v.in.ogr.qgis tab, select the layer that you have just loaded into QGIS and name your output vector map. 
- Once you are done, click "Run", and once it is finished click "View output". A new layer should appear under "Layers"

### Step 2.3: Simplification
Now that we have the world map in QGIS, we can begin simplification. 

**Simplifying with v.generalize**

- Reopen the GRASS toolbox (The icon with tools and grass in the third row of the QGIS toolbar)
- In the "Modules" tab, search for "v.generalize"
- Select your input vector map, which should be the new layer you created in Step 2.1
- For "Feature Type" select "Boundary"
- For "Generalization Algorithim", select "Douglas-Peucker Algorithim"
- For "Maximal Tolerence Value", select a value between 0.1-0.01
- Name your output map (suggest: (original name)-doug)
- Once you are done, click "Run", and once it is finished click "View output". A new layer should appear under "Layers"

**Simplifying with "Simplify" tool**

- Go to Vector > Geometry Tools > Simplify
- Select the world map as the input layer
- Select the "Simplification Layer" and click "Distance (Douglas-Peucker)"
- Change the tolerence to 0.00001
- Once you are done, click "Run". A new layer should appear under "Layers"

**Vertex editing**

- Go to Layer > Toggle Editing
- Go to Edit > Vertex Tool (All Layers). This will allow the movement of the polygon's vertices
- On the map, zoom in to the vertices you wish to edit and move them to how you see fit

Note: To make the polygons snap to lines or other vertices, you can use the Snapping Toolbar. Go to View > Toolbars > Snapping Toolbar and click it to use.

### Step 2.4: Exporting
Once you are finished simplifying the map, you can now export it as a GeoJSON file

- Right click on the finished layer that you want to export
- Go to Export > Save Features as
- Under "Format", select "GeoJSON"
- Select where you want to save the file under "File Name"
- Under "CRS", select "WGS 84"
- Once you are done, click "OK"

The file should now be saved as a GeoJSON in the location you selected under "File Name".
