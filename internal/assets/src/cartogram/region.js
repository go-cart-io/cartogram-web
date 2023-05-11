/**
 * RegionVersion contains data for a version of a map region
 */
export class RegionVersion {

  /**
   * constructor creates a new instance of the RegionVersion class
   * @param {string} name The human-readable name of the version
   * @param {string} unit The unit of the version
   * @param {number} value The value of the version
   * @param {Array<Polygon>} polygons The polygons of the version
   */
  constructor(name, unit, value, polygons) {
      this.name = name;
      this.unit = unit;
      this.value = value;
      this.polygons = polygons;
  }

  toGeoJSON(name, cartogram_id) {

      return {
          type: "Feature",
          properties: {
              cartogram_id: cartogram_id,
              name: name,
              value: this.value,
              unit: this.unit
          },
          geometry: {
              type: "MultiPolygon",
              coordinates: this.polygons.map(polygon => polygon.toGeoJSONCoordinates())
          }

      };

  }
}

/**
* Region contains map data for a region of a conventional map or cartogram
*/
export class Region {

  /**
   * constructor creates a new instance of the Region class
   * @param {string} name The name of the region
   * @param {string} abbreviation The abbreviation of the region
   */
  constructor(name, abbreviation) {
      this.name = name;
      this.abbreviation = abbreviation;

      /**
       * The versions of the region
       * @type {Object.<string, RegionVersion>}
       */
      this.versions = {};
  }

  /**
   * Adds a new version to the region
   * @param {string} sysname The unique system identifier of the version (not necessarily human readable or friendly)
   * @param {RegionVersion} version The new region version
   */
  addVersion(sysname, version) {
      this.versions[sysname] = version;
  }

  /**
   * Returns the region version with sysname
   * @param {string} sysname The sysname of the region version
   * @returns {RegionVersion}
   */
  getVersion(sysname) {
      return this.versions[sysname];
  }


}