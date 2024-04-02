/**
 * Polygon contains data for one D3 polygon
 */
export class Polygon {
  id: string
  path: string
  coordinates: Array<[number, number]>
  holes: Array<Array<[number, number]>>
  representPt: [number, number] | null

  /**
   * constructor creates a new instance of the Polygon class
   * @param {string} id The id of the Path
   * @param {Object} path The D3 line function of the Polygon
   * @param {Array<Array<number,number>>} coordinates The raw coordinates of the Polygon, to be used to rescale the polygon for area equalization
   * @param {Array<Array<Array<number,number>>>} holes The raw holes of the Polygon, to be used to rescale the polygon for area equalization
   */
  constructor(
    id: string,
    path: string,
    coordinates: Array<[number, number]>,
    holes: Array<Array<[number, number]>> = [],
    representPt: [number, number] | null
  ) {
    this.id = id
    this.path = path
    this.coordinates = coordinates
    this.holes = holes
    this.representPt = representPt
  }

  toGeoJSONCoordinates(): Array<Array<[number, number]>> {
    return [this.coordinates].concat(this.holes)
  }
}

/**
 * RegionVersion contains data for a version of a map region
 */
export class RegionVersion {
  name: string
  unit: string
  value: number
  polygons: Array<Polygon>

  /**
   * constructor creates a new instance of the RegionVersion class
   * @param {string} name The human-readable name of the version
   * @param {string} unit The unit of the version
   * @param {number} value The value of the version
   * @param {Array<Polygon>} polygons The polygons of the version
   */
  constructor(name: string, unit: string, value: number, polygons: Array<Polygon>) {
    this.name = name
    this.unit = unit
    this.value = value
    this.polygons = polygons
  }

  toGeoJSON(name: string, cartogram_id: string): object {
    return {
      type: 'Feature',
      properties: {
        cartogram_id: cartogram_id,
        name: name,
        value: this.value,
        unit: this.unit
      },
      geometry: {
        type: 'MultiPolygon',
        coordinates: this.polygons.map((polygon) => polygon.toGeoJSONCoordinates())
      }
    }
  }
}

/**
 * Region contains map data for a region of a conventional map or cartogram
 */
export class Region {
  name: string
  abbreviation: string
  versions: { [key: string]: RegionVersion }

  /**
   * constructor creates a new instance of the Region class
   * @param {string} name The name of the region
   * @param {string} abbreviation The abbreviation of the region
   */
  constructor(name: string, abbreviation: string) {
    this.name = name
    this.abbreviation = abbreviation ? abbreviation : name

    /**
     * The versions of the region
     * @type {Object.<string, RegionVersion>}
     */
    this.versions = {}
  }

  /**
   * Adds a new version to the region
   * @param {string} sysname The unique system identifier of the version (not necessarily human readable or friendly)
   * @param {RegionVersion} version The new region version
   */
  addVersion(sysname: string, version: RegionVersion): void {
    this.versions[sysname] = version
  }

  /**
   * Returns the region version with sysname
   * @param {string} sysname The sysname of the region version
   * @returns {RegionVersion}
   */
  getVersion(sysname: string): RegionVersion {
    return this.versions[sysname]
  }
}
