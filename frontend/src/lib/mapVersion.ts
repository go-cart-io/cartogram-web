import GallPetersProjection from './projection'
import type { Extrema, Labels, Mappack } from './interface'

/**
 * An enum of the supported map data formats.
 * @constant
 * @type {Object<string,number>}
 * @default
 */
export const MapDataFormat = {
  GOCARTJSON: 1,
  GEOJSON: 2
}

/**
 * MapVersionData contains data used to construct a map from raw JSON data
 */
export class MapVersionData {
  regions: {
    [key: string]: {
      polygons: Array<{
        id: string
        coordinates: Array<[number, number]>
        holes: Array<Array<[number, number]>>
      }>
      name: string
      value: number
      abbreviation: string
    }
  }
  name: string
  unit: string
  labels: Labels | null
  world: boolean
  extrema: Extrema

  /**
   * constructor creates an instance of the MapVersionData class from raw map data in JSON
   * @param {Array<{id: string, polygon_id: number, coordinates: Array<Array<number,number>>}>} features
   * @param {Extrema} extrema Extrema for the map version
   * @param {Object} tooltip Tooltip data for the map version
   * @param {string} tooltip.unit
   * @param {string} tooltip.label
   * @param {Object.<string,{name: string, value: number}>} tooltip.data
   * @param {Object.<string,string>} abbreviations A map of region names to abbreviations. Only needs to be specified once per map.
   * @param {Labels} labels Labels for the map version
   * @param {number} format The format of the given map data.
   * @param {boolean} world Whether it is a world map.
   */
  constructor(
    features: any,
    extrema: Extrema,
    tooltip: {
      label: string
      unit: string
      data: { [key: string]: { name: string; value: number } }
    },
    abbreviations: { [key: string]: string } | null = null,
    labels: Labels | null = null,
    format: number = MapDataFormat.GOCARTJSON,
    world: boolean = false
  ) {
    this.regions = {}
    this.name = tooltip.label
    this.unit = tooltip.unit
    this.labels = labels
    this.world = world

    switch (format) {
      case MapDataFormat.GOCARTJSON:
        features.forEach((feature: any) => {
          if (this.regions.hasOwnProperty(feature.id)) {
            this.regions[feature.id].polygons.push({
              id: feature.properties.polygon_id.toString(),
              coordinates: feature.coordinates,
              holes: feature.hasOwnProperty('holes') ? feature.holes : []
            })
          } else {
            this.regions[feature.id] = {
              polygons: [
                {
                  id: feature.properties.polygon_id.toString(),
                  coordinates: feature.coordinates,
                  holes: feature.hasOwnProperty('holes') ? feature.holes : []
                }
              ],
              name: tooltip.data['id_' + feature.id]['name'],
              value: tooltip.data['id_' + feature.id]['value'],
              abbreviation:
                abbreviations !== null
                  ? abbreviations[tooltip.data['id_' + feature.id]['name']]
                  : ''
            }
          }
        }, this)

        break
      case MapDataFormat.GEOJSON:
        var next_polygon_id = 1

        features.forEach((feature: any) => {
          switch (feature.geometry.type) {
            case 'Polygon':
              var polygon_coords
              var polygon_holes = []

              var polygon_id = next_polygon_id.toString()

              for (let i = 0; i < feature.geometry.coordinates.length; i++) {
                /* The first array of coordinates is the outer ring. The rest are holes */
                if (i == 0) {
                  polygon_coords = feature.geometry.coordinates[0]
                  next_polygon_id++
                  continue
                }

                polygon_holes.push(feature.geometry.coordinates[i])
                /* We increase the polygon ID for holes for compatibility reasons. This is what the gen2json
                         Python script does.
                      */
                next_polygon_id++
              }

              /* If the map is a world map, we transform the coordinates
                  using Gall-Peters projection.
                  */
              if (world) {
                let projection = new GallPetersProjection()

                for (let i = 0; i < polygon_coords.length; i++) {
                  polygon_coords[i] = projection.transformLongLat(polygon_coords[i])
                }

                for (let i = 0; i < polygon_holes.length; i++) {
                  for (let j = 0; j < polygon_holes[i].length; j++) {
                    polygon_holes[i][j] = projection.transformLongLat(polygon_holes[i][j])
                  }
                }
              }

              this.regions[feature.properties.cartogram_id] = {
                polygons: [
                  {
                    id: polygon_id,
                    coordinates: polygon_coords,
                    holes: polygon_holes
                  }
                ],
                name: tooltip.data['id_' + feature.properties.cartogram_id]['name'],
                value: tooltip.data['id_' + feature.properties.cartogram_id]['value'],
                abbreviation:
                  abbreviations !== null
                    ? abbreviations[tooltip.data['id_' + feature.properties.cartogram_id]['name']]
                    : ''
              }

              break
            case 'MultiPolygon':
              var polygons: Array<any> = []

              feature.geometry.coordinates.forEach(function (polygon: any) {
                var polygon_coords
                var polygon_holes = []
                var polygon_id = next_polygon_id.toString()

                for (let i = 0; i < polygon.length; i++) {
                  /* The first array of coordinates is the outer ring. The rest are holes */
                  if (i == 0) {
                    polygon_coords = polygon[0]
                    next_polygon_id++
                    continue
                  }

                  polygon_holes.push(polygon[i])
                  next_polygon_id++
                }

                /* If the map is a world map, we transform the coordinates
                      using Gall-Peters projection.
                      */
                if (world) {
                  let projection = new GallPetersProjection()

                  for (let i = 0; i < polygon_coords.length; i++) {
                    polygon_coords[i] = projection.transformLongLat(polygon_coords[i])
                  }

                  for (let i = 0; i < polygon_holes.length; i++) {
                    for (let j = 0; j < polygon_holes[i].length; j++) {
                      polygon_holes[i][j] = projection.transformLongLat(polygon_holes[i][j])
                    }
                  }
                }

                polygons.push({
                  id: polygon_id,
                  coordinates: polygon_coords,
                  holes: polygon_holes
                })
              }, this)

              this.regions[feature.properties.cartogram_id] = {
                polygons: polygons,
                name: tooltip.data['id_' + feature.properties.cartogram_id]['name'],
                value: tooltip.data['id_' + feature.properties.cartogram_id]['value'],
                abbreviation:
                  abbreviations !== null
                    ? abbreviations[tooltip.data['id_' + feature.properties.cartogram_id]['name']]
                    : ''
              }

              break
            default:
              throw "Feature type '" + feature.geometry.type + "' not supported"
          }
        }, this)
        break
      default:
        throw 'Unsupported map format'
    }

    /**
     * @type {Extrema}
     */
    if (world) {
      let projection = new GallPetersProjection()
      this.extrema = {
        min_x: projection.transformLongitude(-180),
        min_y: projection.transformLatitude(-90),
        max_x: projection.transformLongitude(180),
        max_y: projection.transformLatitude(90)
      }
    } else this.extrema = extrema
  }

  static mapVersionDataFromMappack(mappack: Mappack | null, mappackItem: any): MapVersionData {
    let extrema
    let format
    let world = false

    // We check if the map is a world map by searching for the 'extent' key in mappack.original.
    // We then pass a boolean to the MapVersionData constructor.
    if ('extent' in mappackItem) {
      world = mappackItem.extent === 'world'
    }

    // We need to find out the map format. If the extrema is located in the bbox property, then we have GeoJSON. Otherwise, we have the old JSON format.
    if (mappackItem.hasOwnProperty('bbox')) {
      extrema = {
        min_x: mappackItem.bbox[0],
        min_y: mappackItem.bbox[1],
        max_x: mappackItem.bbox[2],
        max_y: mappackItem.bbox[3]
      }
      format = MapDataFormat.GEOJSON
    } else {
      extrema = mappackItem.extrema
      format = MapDataFormat.GOCARTJSON
    }

    return new MapVersionData(
      mappackItem.features,
      extrema,
      mappackItem.tooltip,
      mappack?.abbreviations,
      mappack?.labels,
      format,
      world
    )
  }
}

/**
 * MapVersion contains map data for a version of a conventional map or cartogram
 */
export class MapVersion {
  name: string
  extrema: Extrema
  dimension: { x: number; y: number }
  labels: Labels | null = null
  world: boolean = false
  legendData: {
    versionTotalValue: number | null
    versionOriginalArea: number | null
  }

  /**
   * constructor creates an instance of the MapVersion class
   * @param {string} name The human-readable name of the map version
   * @param {Extrema} extrema Extrema for this map version
   * @param {Array} dimension The width and height of the map version
   * @param {Labels} labels The labels of the map version. Optional.
   */
  constructor(
    name: string,
    extrema: Extrema,
    dimension: { x: number; y: number },
    labels: Labels | null = null,
    world: boolean = false
  ) {
    this.name = name
    this.extrema = extrema
    this.dimension = dimension
    this.labels = labels
    this.world = world
    // legendData stores legend and gridline information of the map version.
    this.legendData = {
      versionTotalValue: null,
      versionOriginalArea: null
    }
  }
}
