/**
 * SVG contains helper methods for drawing SVG objects
 */
export default class SVG {
  /**
   * lineFunction returns a string of SVG path commands for a polygon with holes
   * @param {Function} scaleX A function to scale X coordinates
   * @param {Function} scaleY A function to scale Y coordinates
   * @param {Array} coordinates An array of coordinates for the polygon
   * @param {Array} holes An array of arrays of coordinates for the holes of the polygon
   * @returns {string} The SVG path
   */
  static lineFunction(
    scaleX: Function,
    scaleY: Function,
    coordinates: Array<[number, number]>,
    holes: Array<Array<[number, number]>>
  ): string {
    var path = ''

    for (let i = 0; i < coordinates.length; i++) {
      if (i == 0) {
        path +=
          'M ' + scaleX(coordinates[i]).toString() + ',' + scaleY(coordinates[i]).toString() + ' '
      } else {
        path +=
          'L ' + scaleX(coordinates[i]).toString() + ',' + scaleY(coordinates[i]).toString() + ' '
      }
    }

    path += 'z '

    holes.forEach(function (hole_coords) {
      for (let i = 0; i < hole_coords.length; i++) {
        if (i == 0) {
          path +=
            'M ' + scaleX(hole_coords[i]).toString() + ',' + scaleY(hole_coords[i]).toString() + ' '
        } else {
          path +=
            'L ' + scaleX(hole_coords[i]).toString() + ',' + scaleY(hole_coords[i]).toString() + ' '
        }
      }

      path += 'z '
    })

    return path
  }
}
