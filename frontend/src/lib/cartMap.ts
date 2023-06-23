import tinycolor from 'tinycolor2'
import * as d3 from 'd3'

import Tooltip from './tooltip'
import SVG from './svg'
import { Polygon, Region, RegionVersion } from './region'
import { MapVersion, MapVersionData } from './mapVersion'
import GallPetersProjection from './projection'
import type { MapConfig, PolygonToDraw } from './interface'
/**
 * CartMap contains map data for a conventional map or cartogram. One map can contain several versions. In a map version,
 * the map geography is used to represent a different dataset (e.g. land area in a conventional map version, or GDP or
 * population in a cartogram map version).
 */
export default class CartMap {
  name: string

  /**
   * The map configuration information.
   */
  config: MapConfig

  /**
   * The map colors. The keys are region IDs.
   */
  colors: { [key: string]: string } = {}

  /**
   * The map versions. The keys are version sysnames.
   */
  versions: { [key: string]: MapVersion } = {}

  /**
   * The map regions. The keys are region IDs.
   */
  regions: { [key: string]: Region } = {}

  /**
   * The max width of the map across versions.
   */
  max_width = 0.0

  /**
   * The max height of the map across versions.
   */
  max_height = 0.0

  // Transformation
  angle = 0
  position = [0, 0]
  size = [1, 1]
  stretch = [1, 1]

  /**
   * constructor creates a new instance of the Map class
   * @param {string} name The name of the map or cartogram
   * @param {MapConfig} config The configuration of the map or cartogram
   */
  constructor(name: string, config: MapConfig, scale: number = 1.3) {
    this.name = name
    this.config = {
      dont_draw: config.dont_draw.map((id) => id.toString()),
      elevate: config.elevate.map((id) => id.toString()),
      scale: scale
    }
  }

  getVersionGeoJSON(sysname: string) {
    const version = this.versions[sysname]

    return {
      type: 'FeatureCollection',
      bbox: [
        version.extrema.min_x,
        version.extrema.min_y,
        version.extrema.max_x,
        version.extrema.max_y
      ],
      features: Object.keys(this.regions).map((region_id) =>
        this.regions[region_id]
          .getVersion(sysname)
          .toGeoJSON(this.regions[region_id].name, region_id)
      )
    }
  }

  /**
   * getTotalAreasAndValuesForVersion returns the sum of all region values and area for the specified map version.
   * @param {string} sysname The sysname of the map version
   * @returns {number[]} The total value and area of the specified map version
   */
  getTotalAreasAndValuesForVersion(sysname: string): [number, number] {
    var area = 0
    var sum = 0
    const na_regions: Array<{ id: string; area: number }> = []
    Object.keys(this.regions).forEach((region_id) => {
      var areaValue = 0
      this.regions[region_id].getVersion(sysname).polygons.forEach((polygon: Polygon) => {
        const coordinates = polygon.coordinates

        areaValue += Math.abs(d3.polygonArea(coordinates))

        polygon.holes.forEach(function (hole) {
          areaValue -= Math.abs(d3.polygonArea(hole))
        }, this)
      }, this)

      const regionValue = this.regions[region_id].getVersion(sysname).value

      if (regionValue.toString() !== 'NA') {
        sum += regionValue
      } else {
        na_regions.push({ id: region_id, area: areaValue })
      }

      area += areaValue
    }, this)

    const avg_density = sum / area

    na_regions.forEach(function (na_region) {
      sum += avg_density * na_region.area
    }, this)

    return [area, sum]
  }

  /**
   * getTotalValuesForVersion returns the sum of all region values for the specified map version.
   * @param {string} sysname The sysname of the map version
   * @returns {number} The total value of the specified map version
   */
  getTotalValuesForVersion(sysname: string): number {
    var sum = 0
    Object.keys(this.regions).forEach((region_id) => {
      const regionValue = this.regions[region_id].getVersion(sysname).value

      if (regionValue.toString() !== 'NA') {
        sum += regionValue
      }
    }, this)

    return sum
  }

  /**
   * The following returns the sum of all region polygon area values for the specified map version.
   * @param {string} sysname The sysname of the map version
   * @returns {number} The total value of the specified map version
   */
  getTotalAreaForVersion(sysname: string): number {
    var area = 0
    Object.keys(this.regions).forEach((region_id) => {
      this.regions[region_id].getVersion(sysname).polygons.forEach(function (polygon: Polygon) {
        const coordinates = polygon.coordinates

        const areaValue = d3.polygonArea(coordinates)

        area += areaValue
      })
    }, this)
    return area
  }

  /**
   * addVersion adds a new version to the map. If a version with the specified sysname already exists, it will be overwritten.
   * @param {string} sysname A unique system identifier for the version
   * @param {MapVersionData} data Data for the new map version.
   * @param {string} base_sysname Sysname of the version to be used as the standard for area equalization
   */
  addVersion(sysname: string, data: MapVersionData, base_sysname: string) {
    if (this.versions.hasOwnProperty(sysname)) {
      delete this.versions[sysname]
    }

    // Here, the algorithm tries to equalize maps without distorting its initial width-height proportion. It uses the base version's
    // area as standard (currently, it is always the equal area map) and tries to make other map version's area (e.g population and cartogram map)
    // equal to that by scaling them  up or down as necessary.
    var scale_factors: { [key: string]: { x: number; y: number } } = {}
    var version_dimension: { x: number; y: number }

    const CANVAS_MAX_HEIGHT = 350
    const CANVAS_MAX_WIDTH = 350

    var version_height = CANVAS_MAX_HEIGHT
    var version_width = CANVAS_MAX_WIDTH

    const version_width_geojson = data.extrema.max_x - data.extrema.min_x
    const version_height_geojson = data.extrema.max_y - data.extrema.min_y

    if (version_width_geojson >= version_height_geojson) {
      let ratio_height_by_width = version_height_geojson / version_width_geojson
      version_height = CANVAS_MAX_WIDTH * ratio_height_by_width
    } else {
      let ratio_width_by_height = version_width_geojson / version_height_geojson
      version_width = CANVAS_MAX_HEIGHT * ratio_width_by_height
    }

    if (this.versions.hasOwnProperty(base_sysname)) {
      // Calculate the base version's area to equalise current sysname's area
      const base_version_geojson_area = this.getTotalAreasAndValuesForVersion(base_sysname)[0]
      const base_version_width_geojson =
        this.versions[base_sysname].extrema.max_x - this.versions[base_sysname].extrema.min_x
      const base_version_height_geojson =
        this.versions[base_sysname].extrema.max_y - this.versions[base_sysname].extrema.min_y
      const base_version_width = this.versions[base_sysname].dimension.x / this.config.scale
      const base_version_height = this.versions[base_sysname].dimension.y / this.config.scale
      const area_factor =
        (base_version_height_geojson / base_version_height) *
        (base_version_width_geojson / base_version_width)
      const base_version_area = base_version_geojson_area / area_factor

      // Calculate current sysname's GeoJSON area
      var version_total_area_geojson = 0
      Object.keys(data.regions).forEach((region_id) => {
        let region = data.regions[region_id]

        let version_area_value_geojson = 0
        region.polygons.forEach((polygon: any) => {
          const coordinates = polygon.coordinates

          version_area_value_geojson += Math.abs(d3.polygonArea(coordinates))

          polygon.holes.forEach(function (hole: any) {
            version_area_value_geojson -= Math.abs(d3.polygonArea(hole))
          }, this)
        }, this)
        version_total_area_geojson += version_area_value_geojson
      }, this)

      var version_area =
        version_total_area_geojson /
        ((version_width_geojson / version_width) * (version_height_geojson / version_height))
      const equalization_factor = base_version_area / version_area

      //Update the version_width and version_height with new equalised values
      version_width = version_width * Math.sqrt(equalization_factor)
      version_height = version_height * Math.sqrt(equalization_factor)

      // Diagnostic check to see if areas are equal
      // version_area =  version_total_area_geojson/((version_width_geojson/ version_width) * (version_height_geojson/version_height));
      // console.log( sysname, " Area: ", version_area)
      // console.log( base_sysname, ":", base_version_area)
    }

    scale_factors[sysname] = {
      x: (version_width * this.config.scale) / version_width_geojson,
      y: (version_height * this.config.scale) / version_height_geojson
    }

    version_dimension = {
      x: version_width * this.config.scale,
      y: version_height * this.config.scale
    }

    this.max_width = Math.max(this.max_width, version_dimension.x)
    this.max_height = Math.max(this.max_height, version_dimension.y)

    Object.keys(data.regions).forEach((region_id) => {
      var region = data.regions[region_id]

      var polygons = region.polygons.map(
        (polygon) =>
          new Polygon(
            polygon.id,
            /*d3.svg.line()
                      .x(d => scale_factors[sysname].x * (-1*(data.extrema.min_x) + d[0]))
                      .y(d => scale_factors[sysname].y * ((data.extrema.max_y) - d[1]))
                      .interpolate("linear")(polygon.coordinates),*/
            SVG.lineFunction(
              (d: [number, number]) => scale_factors[sysname].x * (-1 * data.extrema.min_x + d[0]),
              (d: [number, number]) => scale_factors[sysname].y * (data.extrema.max_y - d[1]),
              polygon.coordinates,
              polygon.holes
            ),
            polygon.coordinates,
            polygon.holes
          )
      )

      // Create the region if it doesn't exist.
      // This should only happen when adding the first map version.
      if (!this.regions.hasOwnProperty(region_id)) {
        this.regions[region_id] = new Region(region.name, region.abbreviation)
      }

      this.regions[region_id].addVersion(
        sysname,
        new RegionVersion(data.name, data.unit, region.value, polygons)
      )
    }, this)

    this.versions[sysname] = new MapVersion(
      data.name,
      data.extrema,
      version_dimension,
      data.labels,
      data.world
    )
  }

  /**
   * highlightByID highlights or unhighlights a region depending on the given opacity value.
   * @param {string} region_id The ID of the region to highlight
   * @param {string} color The original color of the region
   * @param {boolean} highlight Whether to highlight or unhighlight the region
   */
  static highlightByID(
    where_drawn: Array<string>,
    region_id: string,
    color: string,
    highlight: boolean
  ) {
    where_drawn.forEach(function (element_id) {
      var polygons = document.getElementsByClassName('path-' + element_id + '-' + region_id)

      for (let i = 0; i < polygons.length; i++) {
        if (highlight) {
          polygons[i].setAttribute('fill', tinycolor(color.toString()).brighten(20).toString())
        } else {
          polygons[i].setAttribute('fill', color)
        }
      }
    })
  }

  /**
   * drawTooltip draws the tooltip for the currently highlighted region.
   * @param {MouseEvent} event Mouse event. Used to place the tooltip next to the cursor
   * @param {string} region_id The ID of the region currently highlighted
   */
  drawTooltip(event: MouseEvent, region_id: string) {
    Tooltip.drawWithEntries(
      event,
      this.regions[region_id].name,
      this.regions[region_id].abbreviation,
      Object.keys(this.regions[region_id].versions).map((sysname, _i, _a) => {
        return {
          name: this.regions[region_id].versions[sysname].name,
          value: this.regions[region_id].versions[sysname].value,
          unit: this.regions[region_id].versions[sysname].unit
        }
      }, this)
    )
  }

  /**
   * drawVersion draws a map version in the element with the given ID. You must add colors to the map before attempting to draw a version.
   * Note that version switching is not supported if you draw a version of a map with labels as the initial version.
   * @param {string} sysname The sysname of the map version
   * @param {string} element_id The element of the ID to place the map
   * @param {Array<string>} where_drawn The elements of the IDs where versions of this map are and will be drawn (including the current element_id). Used for parallel highlighting
   */
  drawVersion(sysname: string, element_id: string, where_drawn: Array<string>) {
    var map_container = document.getElementById(element_id + '-svg')
    var version = this.versions[sysname]
    var version_width = this.versions[sysname].dimension.x
    var version_height = this.versions[sysname].dimension.y

    // status of the pointer(s)
    let pointerangle: number | boolean, // (A)
      pointerposition: [number, number] | null, // (B)
      pointerdistance: number | boolean // (C)

    // Empty the map container element
    while (map_container?.firstChild) {
      map_container.removeChild(map_container.firstChild)
    }

    var canvas = d3
      .select('#' + element_id + '-svg')
      .attr('viewBox', '0 0 ' + this.max_width + ' ' + this.max_height)
      .append('g')

    var polygons_to_draw: Array<{
      region_id: string
      polygon_id: string
      path: string
      color: string
      elevated: boolean
      value: number
    }> = []

    // First we collect the information for each polygon to make using D3 easier.
    Object.keys(this.regions).forEach((region_id) => {
      this.regions[region_id].getVersion(sysname).polygons.forEach((polygon: Polygon) => {
        if (!this.config.dont_draw.includes(polygon.id)) {
          polygons_to_draw.push({
            region_id: region_id,
            polygon_id: polygon.id,
            path: polygon.path,
            color: this.colors[region_id],
            elevated: this.config.elevate.includes(polygon.id),
            value: this.regions[region_id].getVersion(sysname).value
          })
        }
      }, this)
    }, this)

    /* To elevate polygons, we draw the elevated ones last */
    polygons_to_draw.sort(function (p1, p2) {
      if (p1.elevated && !p2.elevated) {
        return 1
      }

      if (!p1.elevated && p2.elevated) {
        return -1
      }

      return 0
    })

    var group = canvas.selectAll().data(polygons_to_draw).enter().append('path')

    var areas = group
      .attr('d', (d) => d.path)
      .attr('id', (d) => 'path-' + element_id + '-' + d.polygon_id)
      /* Giving NA regions a different class prevents them from being highlighted, preserving
           their white fill color.
        */
      .attr(
        'class',
        (d) =>
          'area' +
          ' path-' +
          element_id +
          '-' +
          d.region_id +
          (d.value.toString() === 'NA' ? '-na' : '')
      )
      /* NA regions are filled with white */
      .attr('fill', (d) => (d.value.toString() === 'NA' ? '#CCCCCC' : d.color))
      .attr('stroke', '#000')
      .attr('stroke-width', '0.5')
      .on(
        'mouseenter',
        (function (map, where_drawn) {
          return function (event: MouseEvent, d: any) {
            //CartMap.highlightByID(where_drawn, d.region_id, d.color, true)
            map.drawTooltip(event, d.region_id)
          }
        })(this, where_drawn)
      )
      .on(
        'mousemove',
        (function (map) {
          return function (event: MouseEvent, d: any) {
            map.drawTooltip(event, d.region_id)
          }
        })(this)
      )
      .on(
        'mouseleave',
        (function (map, where_drawn) {
          return function (d: PolygonToDraw) {
            //CartMap.highlightByID(where_drawn, d.region_id, d.color, false)
            Tooltip.hide()
          }
        })(this, where_drawn)
      )

    // https://observablehq.com/@d3/multitouch
    d3.select('#' + element_id)
      .style('cursor', 'grab')
      .on(
        'mousedown touchstart',
        (function (map) {
          return function (event: any) {
            event.preventDefault()
            const t = d3.pointers(event, map)
            pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
            pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
            pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
            d3.select(this).style('cursor', 'grabbing') // (F)
          }
        })(this)
      )
      .on(
        'mouseup touchend',
        (function (map) {
          return function (event: any) {
            pointerposition = null // signals mouse up for (D) and (E)
            d3.select(this).style('cursor', 'grab') // (F)
          }
        })(this)
      )
      .on(
        'mousemove touchmove',
        (function (map) {
          return function (event: any) {
            //map.update(event)
            if (!pointerposition) return // mousemove with the mouse up

            const t = d3.pointers(event, map)

            // (A)
            map.position[0] -= pointerposition[0]
            map.position[1] -= pointerposition[1]
            pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
            map.position[0] += pointerposition[0]
            map.position[1] += pointerposition[1]

            if (t.length > 1) {
              // (B)
              if (pointerangle && typeof pointerangle === 'number') {
                map.angle -= pointerangle
                pointerangle = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
                map.angle += pointerangle
              }
              // (C)
              if (pointerdistance && typeof pointerdistance === 'number') {
                map.size[0] /= pointerdistance
                map.size[1] /= pointerdistance
                pointerdistance = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
                map.size[0] *= pointerdistance
                map.size[1] *= pointerdistance
              }
            }

            map.transformVersion()
            event.preventDefault()
          }
        })(this)
      )
      .on(
        'wheel',
        (function (map) {
          return function (event: any) {
            // (D) and (E), pointerposition also tracks mouse down/up
            if (pointerposition) {
              map.angle += event.wheelDelta / 1000
            } else {
              map.size[0] *= 1 + event.wheelDelta / 1000
              map.size[1] *= 1 + event.wheelDelta / 1000
            }
            map.transformVersion()
            event.preventDefault()
          }
        })(this)
      )

    if (version.labels !== null) {
      /* First draw the text */

      var labels = version.labels

      /*
          I created labels using Inkscape with the maps that were scaled for the purposes of area equalization.
          Scaling the labels like this ensures that they are displayed properly.
          */

      // Label transformation for world map projection
      if (version.world) {
        /* We define the transformations that the label coordinates have to go through:
                 Inkscape SVG -> Longitude & Latitude -> Gall-Peters -> Inkscape SVG
               */

        // 1) Inkscape svg -> longitude latitude
        const xMinLong = -180
        const yMaxLat = 90
        const x2LongLat = (x: number) => x / labels.scale_x + xMinLong
        const y2LongLat = (y: number) => yMaxLat - y / labels.scale_y

        // 2) longlat -> gall peters
        let project = new GallPetersProjection()
        const x2Gall = project.transformLongitude
        const y2Gall = project.transformLatitude

        // 3) gall peters -> inkscape svg
        const xMinGall = project.transformLongitude(-180)
        const yMaxGall = project.transformLatitude(90)
        const gallWidth = project.transformLongitude(180) - xMinGall
        const gallScale = 750 / gallWidth
        const x2Ink = (x: number) => (x - xMinGall) * gallScale
        const y2Ink = (y: number) => (yMaxGall - y) * gallScale

        // We define a pipe function to accumulate the transformations.
        const pipe =
          (...fns: any) =>
          (x: any) =>
            fns.reduce((accumulator: any, currentFunction: any) => currentFunction(accumulator), x)

        const xPipeline = pipe(x2LongLat, x2Gall, x2Ink)
        const yPipeLine = pipe(y2LongLat, y2Gall, y2Ink)

        const scaleX = version_width / ((version.extrema.max_x - version.extrema.min_x) * gallScale)
        const scaleY =
          version_height / ((version.extrema.max_y - version.extrema.min_y) * gallScale)

        var text = canvas.selectAll('text').data(labels.labels).enter().append('text')

        var textLabels = text
          .attr('x', (d) => xPipeline(d.x) * scaleX)
          .attr('y', (d) => yPipeLine(d.y) * scaleY)
          .attr('font-family', 'sans-serif')
          .attr('font-size', '9.5px')
          .attr('fill', '#000')
          .text((d) => d.text)

        var lines = canvas.selectAll('line').data(labels.lines).enter().append('line')

        var labelLines = lines
          .attr('x1', (d) => xPipeline(d.x1) * scaleX)
          .attr('x2', (d) => xPipeline(d.x2) * scaleX)
          .attr('y1', (d) => yPipeLine(d.y1) * scaleY)
          .attr('y2', (d) => yPipeLine(d.y2) * scaleY)
          .attr('stroke-width', 1)
          .attr('stroke', '#000')
      } else {
        // Label transformation for non-World Maps.

        var scale_x =
          version_width / ((version.extrema.max_x - version.extrema.min_x) * labels.scale_x)
        var scale_y =
          version_height / ((version.extrema.max_y - version.extrema.min_y) * labels.scale_y)

        var text = canvas.selectAll('text').data(labels.labels).enter().append('text')

        var textLabels = text
          .attr('x', (d) => d.x * scale_x)
          .attr('y', (d) => d.y * scale_y)
          .attr('font-family', 'sans-serif')
          .attr('font-size', '7.5px')
          .attr('fill', '#000')
          .text((d) => d.text)

        var lines = canvas.selectAll('line').data(labels.lines).enter().append('line')

        var labelLines = lines
          .attr('x1', (d) => d.x1 * scale_x)
          .attr('x2', (d) => d.x2 * scale_x)
          .attr('y1', (d) => d.y1 * scale_y)
          .attr('y2', (d) => d.y2 * scale_y)
          .attr('stroke-width', 1)
          .attr('stroke', '#000')
      }
    }
  }

  transformVersion() {
    d3.selectAll('#map-area-svg g, #cartogram-area-svg g')
      // https://gamedev.stackexchange.com/questions/16719/what-is-the-correct-order-to-multiply-scale-rotation-and-translation-matrices-f
      .attr(
        'transform',
        'translate(' +
          this.position[0] +
          ' ' +
          this.position[1] +
          ') scale(' +
          this.size[0] +
          ' ' +
          this.size[1] +
          ') rotate(' +
          this.angle * (180 / Math.PI) +
          ') scale(' +
          this.stretch[0] +
          ' ' +
          this.stretch[1] +
          ')'
      )
  }

  transformReset() {
    this.angle = 0
    this.position = [0, 0]
    this.size = [1, 1]
    this.stretch = [1, 1]
    this.transformVersion()
  }

  /**
   * switchVersion switches the map version displayed in the element with the given ID with an animation.
   * @param {string} current_sysname The sysname of the currently displayed version
   * @param {string} new_sysname The sysname of the version to be displayed
   * @param {string} element_id The ID of the element containing the map
   */
  switchVersion(current_sysname: string, new_sysname: string, element_id: string) {
    Object.keys(this.regions).forEach((region_id) => {
      var newRegionVersion = this.regions[region_id].versions[new_sysname]

      this.regions[region_id].versions[current_sysname].polygons.forEach((polygon: Polygon) => {
        const newPolygon = newRegionVersion.polygons.find((poly) => poly.id === polygon.id)
        const targetPath = newPolygon?.path || polygon.path

        d3.select('#path-' + element_id + '-' + polygon.id)
          .attr('d', polygon.path)
          .transition()
          .ease(d3.easeCubic)
          .duration(1000)
          .attr('d', targetPath)
        /* Change the color and ensure correct highlighting behavior after animation
                 is complete
              */
        window.setTimeout(() => {
          if (newRegionVersion.value.toString() === 'NA') {
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .setAttribute('fill', '#cccccc')
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .classList.remove('path-' + element_id + '-' + region_id)
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .classList.add('path-' + element_id + '-' + region_id + '-na')
          } else {
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .setAttribute('fill', this.colors[region_id])
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .classList.add('path-' + element_id + '-' + region_id)
            document
              .getElementById('path-' + element_id + '-' + polygon.id)!
              .classList.remove('path-' + element_id + '-' + region_id + '-na')
          }
        }, 800)
      }, this)
    }, this)
  }
}
