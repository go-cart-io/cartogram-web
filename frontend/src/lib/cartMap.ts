import * as d3 from 'd3'
import Tooltip from './tooltip'
import SVG from './svg'
import { Polygon, Region, RegionVersion } from './region'
import { MapVersion, MapVersionData } from './mapVersion'
import GallPetersProjection from './projection'
import type { Mappack, MapConfig } from './interface'

/**
 * CartMap contains map data for a conventional map or cartogram. One map can contain several versions. In a map version,
 * the map geography is used to represent a different dataset (e.g. land area in a conventional map version, or GDP or
 * population in a cartogram map version).
 */
export default class CartMap {
  /**
   * The map configuration information.
   */
  config: MapConfig = { dont_draw: [], elevate: [] }

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

  /**
   * Region that is highlighed
   */
  highlighted_region: string | null = null

  /**
   * constructor creates a new instance of the Map class
   * @param {Mappack} mappack The data of the map and cartogram
   */
  init(mappack: Mappack): string {
    let data_names = mappack.config.data_names || ['original', 'population']
    let versionName = '0-base'

    this.addVersion('0-base', mappack, mappack[data_names[0]], '0-base')
    for (let i = 1; i < data_names.length; i++) {
      versionName = i.toString() + '-' + data_names[i]
      this.addVersion(versionName, null, mappack[data_names[i]], '0-base')
    }
    
    /*
      The keys in the colors.json file are prefixed with id_. We iterate through the regions and extract the color
      information from colors.json to produce a color map where the IDs are plain region IDs, as required by
      CartMap.
      */
    var colors: { [key: string]: string } = {}
    Object.keys(this.regions).forEach(function (region_id) {
      colors[region_id] = mappack.colors['id_' + region_id]
    })
    this.colors = colors

    this.config = {
      dont_draw: mappack.config.dont_draw.map((id) => id.toString()),
      elevate: mappack.config.elevate.map((id) => id.toString())
    }
    if (mappack.config.label_size) this.config.label_size = mappack.config.label_size

    return versionName
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
  getTotalAreasAndValuesForVersion(regions: { [key: string]: any }): [number, number] {
    var area = 0
    var sum = 0
    const na_regions: Array<{ id: string; area: number }> = []
    Object.keys(regions).forEach((region_id) => {
      let region = regions[region_id]
      var areaValue = 0
      region.polygons.forEach((polygon: Polygon) => {
        const coordinates = polygon.coordinates

        areaValue += Math.abs(d3.polygonArea(coordinates))

        polygon.holes.forEach(function (hole) {
          areaValue -= Math.abs(d3.polygonArea(hole))
        }, this)
      }, this)

      const regionValue = region.value
      if (regionValue && regionValue.toString() !== 'NA') {
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
   * addVersion adds a new version to the map. If a version with the specified sysname already exists, it will be overwritten.
   * @param {string} sysname A unique system identifier for the version
   * @param {MapVersionData} data Data for the new map version.
   * @param {string} base_sysname Sysname of the version to be used as the standard for area equalization
   */
  addVersion(sysname: string, mappack: Mappack | null, mappackItem: any, base_sysname: string) {
    var data = MapVersionData.mapVersionDataFromMappack(mappack, mappackItem)

    if (this.versions.hasOwnProperty(sysname)) {
      delete this.versions[sysname]
    }

    // Here, the algorithm tries to equalize maps without distorting its initial width-height proportion. It uses the base version's
    // area as standard (currently, it is always the equal area map) and tries to make other map version's area (e.g population and cartogram map)
    // equal to that by scaling them  up or down as necessary.
    var scale_factors: { [key: string]: { x: number; y: number } } = {}
    var version_dimension: { x: number; y: number }

    const MAX_SIZE = 350
    var version_height = MAX_SIZE
    var version_width = MAX_SIZE

    const version_width_geojson = data.extrema.max_x - data.extrema.min_x
    const version_height_geojson = data.extrema.max_y - data.extrema.min_y

    if (version_width_geojson >= version_height_geojson) {
      let ratio_height_by_width = version_height_geojson / version_width_geojson
      version_height = MAX_SIZE * ratio_height_by_width
    } else {
      let ratio_width_by_height = version_width_geojson / version_height_geojson
      version_width = MAX_SIZE * ratio_width_by_height
    }

    var [version_total_area_geojson, version_value] = this.getTotalAreasAndValuesForVersion(
      data.regions
    )
    var version_area =
      version_total_area_geojson /
      ((version_width_geojson / version_width) * (version_height_geojson / version_height))

    // Get the base version's area to equalise current sysname's area
    if (this.versions.hasOwnProperty(base_sysname)) {
      const base_version_area = this.versions[base_sysname].legendData.versionOriginalArea || 0
      const equalization_factor = base_version_area / version_area

      //Update the version_width and version_height with new equalised values
      version_width = version_width * Math.sqrt(equalization_factor)
      version_height = version_height * Math.sqrt(equalization_factor)
      version_area = base_version_area

      // Diagnostic check to see if areas are equal
      // var test_version_area = version_total_area_geojson / ((version_width_geojson / version_width) * (version_height_geojson / version_height))
      // console.log(sysname, ' Area: ', test_version_area)
      // console.log(base_sysname, ':', base_version_area)
    }

    scale_factors[sysname] = {
      x: version_width / version_width_geojson,
      y: version_height / version_height_geojson
    }

    version_dimension = {
      x: version_width,
      y: version_height
    }

    this.max_width = Math.max(this.max_width, version_dimension.x)
    this.max_height = Math.max(this.max_height, version_dimension.y)

    Object.keys(data.regions).forEach((region_id) => {
      var region = data.regions[region_id]

      var polygons = region.polygons.map((polygon) => {
        var scaleX = (d: [number, number]) =>
          scale_factors[sysname].x * (-1 * data.extrema.min_x + d[0])
        var scaleY = (d: [number, number]) => scale_factors[sysname].y * (data.extrema.max_y - d[1])

        return new Polygon(
          polygon.id,
          SVG.lineFunction(scaleX, scaleY, polygon.coordinates, polygon.holes),
          polygon.coordinates,
          polygon.holes,
          polygon.representPt ? [scaleX(polygon.representPt), scaleY(polygon.representPt)] : null
        )
      })

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
    this.versions[sysname].legendData.versionOriginalArea = version_area
    this.versions[sysname].legendData.versionTotalValue = version_value
    this.versions[sysname].unit = data.unit
  }

  /**
   * highlightByID highlights or unhighlights a region depending on the given opacity value.
   * @param {string} region_id The ID of the region to highlight
   * @param {string} color The original color of the region
   * @param {boolean} highlight Whether to highlight or unhighlight the region
   */
  highlightByID(where_drawn: Array<string>, region_id: string) {
    if (!this.highlighted_region) this.unhighlight(where_drawn)

    this.highlighted_region = region_id
    where_drawn.forEach(function (element_id) {
      var polygons = document.getElementsByClassName('path-' + element_id + '-' + region_id)

      for (let i = 0; i < polygons.length; i++) {
        polygons[i].setAttribute('stroke-width', '2')
      }
    })
  }

  unhighlight(where_drawn: Array<string>) {
    if (!this.highlighted_region) return

    var region_id = this.highlighted_region
    where_drawn.forEach(function (element_id) {
      var polygons = document.getElementsByClassName('path-' + element_id + '-' + region_id)

      for (let i = 0; i < polygons.length; i++) {
        polygons[i].setAttribute('stroke-width', '0.5')
      }
    })
    this.highlighted_region = null
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
      representPt: [number, number] | null
      abbreviation: string
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
            representPt: polygon.representPt,
            abbreviation: this.regions[region_id].abbreviation,
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

    var group = canvas.selectAll().data(polygons_to_draw).enter()

    group
      .append('path')
      .attr('d', (d) => d.path)
      .attr('id', (d) => 'path-' + element_id + '-' + d.polygon_id)
      /* Giving NA regions a different class prevents them from being highlighted, preserving
           their white fill color.
        */
      .attr(
        'class',
        (d) =>
          'area path-' + element_id + '-' + d.region_id + (d.value.toString() === 'NA' ? '-na' : '')
      )
      /* NA regions are filled with white */
      .attr('fill', (d) => (d.value.toString() === 'NA' ? '#CCCCCC' : d.color))
      .attr('stroke', '#000')
      .attr('stroke-width', '0.5')
      .attr('vector-effect', 'non-scaling-stroke')
      .on(
        'mouseenter',
        (function (map, where_drawn) {
          return function (event: MouseEvent, d: any) {
            map.highlightByID(where_drawn, d.region_id)
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
          return function (event: MouseEvent, d: any) {
            map.unhighlight(where_drawn)
            Tooltip.hide()
          }
        })(this, where_drawn)
      )

    canvas.attr('font-size', '7px')
    if (version.labels == null) {
      if (this.config.label_size) canvas.attr('font-size', this.config.label_size)
      canvas.attr('text-anchor', 'middle')

      canvas
        .selectAll()
        .data(
          polygons_to_draw.filter(function (d) {
            return d.representPt !== null
          })
        )
        .enter()
        .append('text')
        .attr('id', (d) => 'label-' + element_id + '-' + d.polygon_id)
        .attr('x', (d) => (d.representPt ? d.representPt[0] : 0))
        .attr('y', (d) => (d.representPt ? d.representPt[1] : 0))
        .text((d) => d.abbreviation)
    } else {
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
          .text((d) => d.text)

        var lines = canvas.selectAll('line').data(labels.lines).enter().append('line')

        var labelLines = lines
          .attr('x1', (d) => xPipeline(d.x1) * scaleX)
          .attr('x2', (d) => xPipeline(d.x2) * scaleX)
          .attr('y1', (d) => yPipeLine(d.y1) * scaleY)
          .attr('y2', (d) => yPipeLine(d.y2) * scaleY)
      } else {
        // Label transformation for non-World Maps.
        var scale_x =
          version_width / ((version.extrema.max_x - version.extrema.min_x) * labels.scale_x)
        var scale_y =
          version_height / ((version.extrema.max_y - version.extrema.min_y) * labels.scale_y)

        var text = canvas.selectAll('text').data(labels.labels).enter().append('text')

        var textLabels = text
          .text((d) => d.text)
          .attr('x', (d) => d.x * scale_x)
          .attr('y', (d) => d.y * scale_y)

        var lines = canvas.selectAll('line').data(labels.lines).enter().append('line')

        var labelLines = lines
          .attr('x1', (d) => d.x1 * scale_x)
          .attr('x2', (d) => d.x2 * scale_x)
          .attr('y1', (d) => d.y1 * scale_y)
          .attr('y2', (d) => d.y2 * scale_y)
      }
    }
  }

  /**
   * switchVersion switches the map version displayed in the element with the given ID with an animation.
   * @param {string} currentVersionName The sysname of the currently displayed version
   * @param {string} new_sysname The sysname of the version to be displayed
   * @param {string} element_id The ID of the element containing the map
   */
  switchVersion(currentVersionName: string, new_sysname: string, element_id: string) {
    Object.keys(this.regions).forEach((region_id) => {
      var newRegionVersion = this.regions[region_id].versions[new_sysname]

      this.regions[region_id].versions[currentVersionName].polygons.forEach((polygon: Polygon) => {
        const newPolygon = newRegionVersion.polygons.find((poly) => poly.id === polygon.id)
        if (!newPolygon) return
        const targetPath = newPolygon?.path || polygon.path

        d3.select('#path-' + element_id + '-' + polygon.id)
          .attr('d', polygon.path)
          .transition()
          .ease(d3.easeCubic)
          .duration(1000)
          .attr('d', targetPath)

        // d3.select('#path-' + element_id + '-' + polygon.id)
        //   .transition()
        //   .duration(1000)
        //   .attrTween('d', function (d) {
        //     return interpolatePath(polygon.path, targetPath)
        //   })

        if (newPolygon.representPt) {
          d3.select('#label-' + element_id + '-' + polygon.id)
            .transition()
            .duration(1000)
            .attr('x', newPolygon.representPt[0])
            .attr('y', newPolygon.representPt[1])
        }

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
