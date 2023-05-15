/**
 * Polygon contains data for one D3 polygon
 */
export default class Polygon {
  /**
   * constructor creates a new instance of the Polygon class
   * @param {string} id The id of the Path
   * @param {Object} path The D3 line function of the Polygon
   * @param {Array<Array<number,number>>} coordinates The raw coordinates of the Polygon, to be used to rescale the polygon for area equalization
   * @param {Array<Array<Array<number,number>>>} holes The raw holes of the Polygon, to be used to rescale the polygon for area equalization
   */
  constructor(id, path, coordinates, holes = []) {
    /**
     * The Polygon ID
     * @type {string}
     */
    this.id = id

    /**
     * The Polygon D3 line function
     * @type {Object}
     */
    this.path = path

    this.coordinates = coordinates

    this.holes = holes
  }

  toGeoJSONCoordinates() {
    return [this.coordinates].concat(this.holes)
  }
}
