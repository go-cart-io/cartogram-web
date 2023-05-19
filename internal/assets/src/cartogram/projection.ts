/**
 * WorldMapProjection is an abstract class which contains methods for transforming
 * longitude and latitude to a different projection.
 */
export class WorldMapProjection {
  constructor() {
    if (this.constructor == WorldMapProjection)
      throw new Error('Abstract classes cannot be instantiated.')
  }

  transformLongitude(longitude: number): number {
    throw new Error("Method 'transformLongitude()' must be implemented.")
  }

  transformLatitude(latitude: number): number {
    throw new Error("Method 'transformLatitude()' must be implemented.")
  }

  transformLongLat(longlat: Array<number>): Array<number> {
    return [this.transformLongitude(longlat[0]), this.transformLatitude(longlat[1])]
  }
}

/**
 * GallPetersProjection is a concrete class that implements the methods in WorldMapProjection.
 */

export default class GallPetersProjection extends WorldMapProjection {
  constructor() {
    super()
  }

  transformLongitude(longitude: number): number {
    let longitudeInRadians = (longitude * Math.PI) / 180
    return (longitudeInRadians * 100) / Math.SQRT2
  }

  transformLatitude(latitude: number): number {
    let latitudeInRadians = (latitude * Math.PI) / 180
    return 100 * Math.SQRT2 * Math.sin(latitudeInRadians)
  }
}
