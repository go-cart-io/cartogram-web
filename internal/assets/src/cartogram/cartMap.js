import * as d3 from 'd3'
import tinycolor from 'tinycolor2'

import Tooltip from './tooltip.js'
import SVG from './svg.js'
import Polygon from './polygon.js'
import { Region, RegionVersion } from './region.js'
import { MapVersion, MapVersionData } from './mapVersion.js'
import GallPetersProjection from './projection.js'

/**
 * CartMap contains map data for a conventional map or cartogram. One map can contain several versions. In a map version,
 * the map geography is used to represent a different dataset (e.g. land area in a conventional map version, or GDP or
 * population in a cartogram map version).
 */
export default class CartMap {
  /**
   * constructor creates a new instance of the Map class
   * @param {string} name The name of the map or cartogram
   * @param {MapConfig} config The configuration of the map or cartogram
   */
  constructor(name, config, scale = 1.3) {
    this.name = name

    /**
     * The map configuration information.
     * @type {MapConfig}
     */
    this.config = {
      dont_draw: config.dont_draw.map((id) => id.toString()),
      elevate: config.elevate.map((id) => id.toString()),
      scale: scale
    }

    /**
     * The map colors. The keys are region IDs.
     * @type {Object.<string,string>}
     */
    this.colors = {}

    /**
     * The map versions. The keys are version sysnames.
     * @type {Object.<string,MapVersion>}
     */
    this.versions = {}

    /**
     * The map regions. The keys are region IDs.
     * @type {Object.<string,Region>}
     */
    this.regions = {}

    /**
     * The max width of the map across versions.
     * @type {number}
     */
    this.max_width = 0.0

    /**
     * The max height of the map across versions.
     */
    this.max_height = 0.0
  }

  getVersionGeoJSON(sysname) {
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
   * getConvenLegendUnit returns the a legend unit of the conventional map
   * @param {string} sysname The sysname of the map version
   * @returns {string} The legend unit of the map
   */
  getLegendUnit(sysname) {
    var unit = ''
    Object.keys(this.regions).forEach(function (region_id) {
      unit = this.regions[region_id].getVersion(sysname).unit
    }, this)
    return unit
  }

  /**
   * The following returns the scaling factors (x and y) of map of specified version.
   * @param {string} sysname The sysname of the map version
   * @returns {number[]} The total polygon area of the specified map version
   */
  getVersionPolygonScale(sysname) {
    const version_width =
      this.versions[sysname].extrema.max_x -
      this.versions[sysname].extrema.min_x
    const version_height =
      this.versions[sysname].extrema.max_y -
      this.versions[sysname].extrema.min_y

    const scale_x = this.versions[sysname].dimension.x / version_width
    const scale_y = this.versions[sysname].dimension.y / version_height

    return [scale_x, scale_y]
  }

  /**
   * getTotalAreasAndValuesForVersion returns the sum of all region values and area for the specified map version.
   * @param {string} sysname The sysname of the map version
   * @returns {number[]} The total value and area of the specified map version
   */
  getTotalAreasAndValuesForVersion(sysname) {
    var area = 0
    var sum = 0
    const na_regions = []
    Object.keys(this.regions).forEach(function (region_id) {
      var areaValue = 0
      this.regions[region_id]
        .getVersion(sysname)
        .polygons.forEach(function (polygon) {
          const coordinates = polygon.coordinates

          areaValue += Math.abs(d3.polygonArea(coordinates))

          polygon.holes.forEach(function (hole) {
            areaValue -= Math.abs(d3.polygonArea(hole))
          }, this)
        }, this)

      const regionValue = this.regions[region_id].getVersion(sysname).value

      if (regionValue !== 'NA') {
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
  getTotalValuesForVersion(sysname) {
    var sum = 0
    Object.keys(this.regions).forEach(function (region_id) {
      const regionValue = this.regions[region_id].getVersion(sysname).value

      if (regionValue != 'NA') {
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
  getTotalAreaForVersion(sysname) {
    var area = 0
    Object.keys(this.regions).forEach(function (region_id) {
      this.regions[region_id]
        .getVersion(sysname)
        .polygons.forEach(function (polygon) {
          const coordinates = polygon.coordinates

          const areaValue = d3.polygonArea(coordinates)

          area += areaValue
        })
    }, this)
    return area
  }

  /**
   * Determines if the computed legend area and value is correct
   * @param sysname
   * @param width
   * @param value
   */
  verifyLegend(sysname, squareWidth, valuePerSquare) {
    const [scaleX, scaleY] = this.getVersionPolygonScale(sysname)
    const [versionArea, versionTotalValue] =
      this.getTotalAreasAndValuesForVersion(sysname)
    const tolerance = 0.001

    const legendTotalValue =
      (valuePerSquare * (versionArea * scaleX * scaleY)) /
      (squareWidth * squareWidth)

    if (!(Math.abs(versionTotalValue - legendTotalValue) < tolerance)) {
      console.warn(
        `The legend value (${valuePerSquare}) and width (${squareWidth}px) for ${sysname} is not correct. Calculating the total value from the legend yields ${legendTotalValue}, but it should be ${versionTotalValue}`
      )
    } else {
      console.log(
        `The legend value (${valuePerSquare}) and width (${squareWidth}px) for ${sysname} is correct (calculated total value=${legendTotalValue}, actual total value=${versionTotalValue})`
      )
    }
  }

  /**
   * Calculates legend information of the map version
   * @param {string} sysname The sysname of the map version
   */
  getLegendData(sysname) {
    // Get unit for the map version.
    const unit = this.getLegendUnit(sysname)

    // Obtain the scaling factors, area and total value for this map version.
    const [scaleX, scaleY] = this.getVersionPolygonScale(sysname)
    const [versionArea, versionTotalValue] =
      this.getTotalAreasAndValuesForVersion(sysname)
    const valuePerPixel = versionTotalValue / (versionArea * scaleX * scaleY)

    // Each square to be in the whereabouts of 1% of versionTotalValue.
    let valuePerSquare = versionTotalValue / 100
    let widthA = Math.sqrt(valuePerSquare / valuePerPixel)

    // If width is too small, we increment the percentage.
    while (widthA < 20) {
      valuePerSquare *= 2
      widthA = Math.sqrt(valuePerSquare / valuePerPixel)
    }

    let widthB = widthA
    let widthC = widthA

    // Declare and assign variables for valuePerSquare's power of 10 and "nice number".
    let scalePowerOf10 = Math.floor(Math.log10(valuePerSquare))
    let scaleNiceNumberA = 99
    let scaleNiceNumberB
    let scaleNiceNumberC

    // We find the "nice number" that is closest to valuePerSquare's
    const valueFirstNumber = valuePerSquare / Math.pow(10, scalePowerOf10)
    let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumberA)

    const niceNumbers = [1, 2, 5, 10]
    niceNumbers.forEach(function (n) {
      if (Math.abs(valueFirstNumber - n) < valueDiff) {
        valueDiff = Math.abs(valueFirstNumber - n)
        scaleNiceNumberA = n
      }
    })

    if (scaleNiceNumberA == 1) {
      scaleNiceNumberB = 2
      scaleNiceNumberC = 5
    } else if (scaleNiceNumberA == 2) {
      scaleNiceNumberB = 5
      scaleNiceNumberC = 10
    } else if (scaleNiceNumberA == 5) {
      scaleNiceNumberB = 10
      scaleNiceNumberC = 20
    } else {
      scaleNiceNumberA = 1
      scaleNiceNumberB = 2
      scaleNiceNumberC = 5
      scalePowerOf10 += 1
    }

    widthA *= Math.sqrt(
      (scaleNiceNumberA * Math.pow(10, scalePowerOf10)) / valuePerSquare
    )
    widthB *= Math.sqrt(
      (scaleNiceNumberB * Math.pow(10, scalePowerOf10)) / valuePerSquare
    )
    widthC *= Math.sqrt(
      (scaleNiceNumberC * Math.pow(10, scalePowerOf10)) / valuePerSquare
    )

    const gridPathA = this.getGridPath(widthA, this.max_width, this.max_height)
    const gridPathB = this.getGridPath(widthB, this.max_width, this.max_height)
    const gridPathC = this.getGridPath(widthC, this.max_width, this.max_height)

    // Store legend Information
    this.versions[sysname].legendData.gridData.gridA.width = widthA
    this.versions[sysname].legendData.gridData.gridB.width = widthB
    this.versions[sysname].legendData.gridData.gridC.width = widthC

    this.versions[sysname].legendData.gridData.gridA.scaleNiceNumber =
      scaleNiceNumberA
    this.versions[sysname].legendData.gridData.gridB.scaleNiceNumber =
      scaleNiceNumberB
    this.versions[sysname].legendData.gridData.gridC.scaleNiceNumber =
      scaleNiceNumberC

    this.versions[sysname].legendData.gridData.gridA.gridPath = gridPathA
    this.versions[sysname].legendData.gridData.gridB.gridPath = gridPathB
    this.versions[sysname].legendData.gridData.gridC.gridPath = gridPathC

    this.versions[sysname].legendData.scalePowerOf10 = scalePowerOf10
    this.versions[sysname].legendData.unit = unit
    this.versions[sysname].legendData.versionTotalValue = versionTotalValue
  }

  /**
   * The following draws the static legend for each map
   * @param {string} sysname The sysname of the map version
   * @param {string} legendSVGID The html id used for legend SVG display
   * @param {string} old_sysname The previous sysname after map version switch. Optional.
   * @param {boolean} change_map True if the map is displayed for the first time or the map is changed. Optional.
   */
  drawLegend(sysname, legendSVGID, old_sysname = null, change_map = false) {
    this.getLegendData(sysname)
    const legendSVG = d3.select('#' + legendSVGID)

    // Remove existing child nodes
    legendSVG.selectAll('*').remove()

    // We get the current selected user grid path to draw our static legend

    let currentGridPath = legendSVG.attr('data-current-grid-path')
    let prevLegendType = legendSVG.attr('data-legend-type')

    // Get the transitionWidth which is previously selected grid path. This value helps in transitioning
    // from static legend to resizable legend.
    let transitionWidth

    // When switching between static and selectable legend.
    if (change_map == true) {
      transitionWidth = this.versions[sysname].legendData.gridData.gridA.width
    } else if (old_sysname == null) {
      transitionWidth = this.versions[sysname].legendData.gridData.gridC.width
    }
    // When switching between versions
    else {
      if (prevLegendType == 'static') {
        transitionWidth =
          this.versions[old_sysname].legendData['gridData'][currentGridPath][
            'width'
          ]
      } else {
        transitionWidth =
          this.versions[old_sysname].legendData.gridData.gridC.width
      }
    }

    // Retrive legend information
    const unit = this.versions[sysname].legendData.unit
    const versionTotalValue =
      this.versions[sysname].legendData.versionTotalValue
    const width =
      this.versions[sysname].legendData['gridData'][currentGridPath]['width']

    const scaleNiceNumber =
      this.versions[sysname].legendData['gridData'][currentGridPath][
        'scaleNiceNumber'
      ]
    const scalePowerOf10 = this.versions[sysname].legendData.scalePowerOf10

    const legendSquare = legendSVG
      .append('rect')
      .attr('id', legendSVGID + 'A')
      .attr('x', '20') // Padding of 20px on the left
      .attr('y', '5')
      .attr('fill', '#FFFFFF')
      .attr('stroke', '#AAAAAA')
      .attr('stroke-width', '2px')
      .attr('width', transitionWidth)
      .attr('height', transitionWidth)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', width)
      .attr('height', width)

    const legendText = legendSVG
      .append('text')
      .attr('id', 'legend-text')
      .attr('fill', '#5A5A5A')
      .attr('dy', '0.3em') // vertical alignment
      .attr('opacity', 0)

    // Set "x" and "y" of legend text relative to square's width
    legendText
      .attr('x', (20 + width + 15).toString() + 'px')
      .attr('y', (5 + width * 0.5).toString() + 'px')

    // Set legend text
    legendText.append('tspan').text(' = ')

    legendText
      .append('tspan')
      .attr('id', legendSVGID + '-number')
      .text('9999')

    legendText
      .append('tspan')
      .attr('id', legendSVGID + '-unit')
      .text(' placeholder')

    const largeNumberNames = { 6: ' million', 9: ' billion' }

    if (scalePowerOf10 > -4 && scalePowerOf10 < 12) {
      if (scalePowerOf10 in largeNumberNames) {
        d3.select('#' + legendSVGID + '-number').text(scaleNiceNumber)
        d3.select('#' + legendSVGID + '-unit').text(
          ' ' + largeNumberNames[scalePowerOf10] + ' ' + unit
        )
      } else if (scalePowerOf10 > 9) {
        d3.select('#' + legendSVGID + '-number').text(
          scaleNiceNumber * Math.pow(10, scalePowerOf10 - 9)
        )
        d3.select('#' + legendSVGID + '-unit').text(' billion ' + unit)
      } else if (scalePowerOf10 > 6) {
        d3.select('#' + legendSVGID + '-number').text(
          scaleNiceNumber * Math.pow(10, scalePowerOf10 - 6)
        )
        d3.select('#' + legendSVGID + '-unit').text(' million ' + unit)
      } else {
        d3.select('#' + legendSVGID + '-number').text(
          (scaleNiceNumber * Math.pow(10, scalePowerOf10))
            .toLocaleString()
            .split(',')
            .join(' ')
        )
        d3.select('#' + legendSVGID + '-unit').text(' ' + unit)
      }

      // Adjust multiplier
      d3.select('#' + legendSVGID + '-multiplier').text(
        Math.pow(10, scalePowerOf10).toLocaleString().split(',').join(' ')
      )
    }
    // If scalePowerOf10 is too extreme, we use scientific notation
    else {
      d3.select('#' + legendSVGID + '-number').text(scaleNiceNumber)
      d3.select('#' + legendSVGID + '-unit').html(' &#xD7; 10')
      legendText
        .append('tspan')
        .text(scalePowerOf10)
        .style('font-size', '10px')
        .attr('dy', '-10px')
      legendText.append('tspan').text(unit).attr('dy', '10px').attr('dx', '8px')
    }

    // Set "y" of total value text to be 20px below the top of the square.
    const totalValue = legendSVG
      .append('text')
      .attr('id', 'total-text')
      .attr('x', '20') // Padding of 20px on the left
      .attr('fill', '#5A5A5A')
      .attr('opacity', 0)

    const total_value_Y = 5 + parseInt(width) + 20
    totalValue.attr('y', total_value_Y.toString() + 'px')

    // Set total value text.
    const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
    if (totalScalePowerOfTen > -4 && totalScalePowerOfTen < 12) {
      if (totalScalePowerOfTen in largeNumberNames)
        totalValue.text(
          'Total: ' +
            (
              versionTotalValue / Math.pow(10, totalScalePowerOfTen)
            ).toPrecision(3) +
            ' ' +
            largeNumberNames[totalScalePowerOfTen] +
            ' ' +
            unit
        )
      else if (totalScalePowerOfTen > 9)
        totalValue.text(
          'Total: ' +
            (versionTotalValue / Math.pow(10, 9)).toPrecision(3) +
            ' billion ' +
            unit
        )
      else if (totalScalePowerOfTen > 6)
        totalValue.text(
          'Total: ' +
            (versionTotalValue / Math.pow(10, 6)).toPrecision(3) +
            ' million ' +
            unit
        )
      // Else we display the total as it is
      else
        totalValue.text(
          'Total: ' +
            versionTotalValue.toLocaleString().split(',').join(' ') +
            ' ' +
            unit
        )
    }
    // If totalScalePowerOfTen is too extreme, we use scientific notation
    else {
      totalValue
        .append('tspan')
        .html(
          'Total : ' +
            (
              versionTotalValue / Math.pow(10, totalScalePowerOfTen)
            ).toPrecision(3) +
            ' &#xD7; 10'
        )
      totalValue
        .append('tspan')
        .text(totalScalePowerOfTen)
        .style('font-size', '10px')
        .attr('dy', '-10px')
      totalValue.append('tspan').text(unit).attr('dy', '10px').attr('dx', '8px')
    }

    // Set different legend text transition duration so that legend text doesn't overlap with legend square transition
    let legendTextsTransitionDuration = 1000
    if (change_map == true) {
      legendTextsTransitionDuration = 1000
    } else if (old_sysname != null) {
      if (prevLegendType == 'static') {
        legendTextsTransitionDuration = 800
      }
    } else if (currentGridPath == 'gridC') {
      legendTextsTransitionDuration = 1000
    } else if (currentGridPath == 'gridB') {
      legendTextsTransitionDuration = 650
    } else if (currentGridPath == 'gridA') {
      legendTextsTransitionDuration = 600
    }

    legendText
      .transition()
      .ease(d3.easeCubic)
      .delay(1000 - legendTextsTransitionDuration)
      .duration(legendTextsTransitionDuration)
      .attr('opacity', 1)

    totalValue
      .transition()
      .ease(d3.easeCubic)
      .delay(1000 - legendTextsTransitionDuration)
      .duration(legendTextsTransitionDuration)
      .attr('opacity', 1)

    // Accommodate enough space so that even the resizable legend also fits in; it keeps the customise, download, share
    // buttons on place
    let legendSVGHeight = width
    Object.keys(this.versions).forEach(function (version_sysname) {
      legendSVGHeight = Math.max(
        legendSVGHeight,
        this.versions[version_sysname].legendData.gridData.gridC.width
      )
    }, this)

    // Adjust height of legendSVG
    legendSVG.attr('height', legendSVGHeight + 30)

    // Verify if legend is accurate
    this.verifyLegend(
      sysname,
      width,
      scaleNiceNumber * Math.pow(10, scalePowerOf10)
    )

    // Update Selected Legend Type in SVG Data
    document.getElementById(legendSVGID).dataset.legendType = 'static'
  }

  /**
   * The following draws the resizable legend for each map
   * @param {string} sysname The sysname of the map version
   * @param {string} legendSVGID The html id used for legend SVG display
   * @param {string} old_sysname The previous sysname after map version switch. Optional.
   */
  drawResizableLegend(sysname, legendSVGID, old_sysname = null) {
    this.getLegendData(sysname)

    const legendSVG = d3.select('#' + legendSVGID)

    // Remove existing child nodes
    legendSVG.selectAll('*').remove()

    // Retrive legend information
    const unit = this.versions[sysname].legendData.unit
    const versionTotalValue =
      this.versions[sysname].legendData.versionTotalValue
    const scalePowerOf10 = this.versions[sysname].legendData.scalePowerOf10
    const widthA = this.versions[sysname].legendData.gridData.gridA.width
    const widthB = this.versions[sysname].legendData.gridData.gridB.width
    const widthC = this.versions[sysname].legendData.gridData.gridC.width
    const scaleNiceNumberA =
      this.versions[sysname].legendData.gridData.gridA.scaleNiceNumber
    const scaleNiceNumberB =
      this.versions[sysname].legendData.gridData.gridB.scaleNiceNumber
    const scaleNiceNumberC =
      this.versions[sysname].legendData.gridData.gridC.scaleNiceNumber
    const gridA = this.versions[sysname].legendData.gridData.gridA.gridPath
    const gridB = this.versions[sysname].legendData.gridData.gridB.gridPath
    const gridC = this.versions[sysname].legendData.gridData.gridC.gridPath

    // We get currently selected grid path (i.e. whether "gridA", "gridB", or "gridC") and type of legend
    let currentGridPath = legendSVG.attr('data-current-grid-path')
    let prevLegendType = legendSVG.attr('data-legend-type')

    // Get legend width data of previous version/ previous static legend
    let transitionWidthA
    let transitionWidthB
    let transitionWidthC

    // When switching between static and selectable legend.
    if (old_sysname == null) {
      transitionWidthA =
        transitionWidthB =
        transitionWidthC =
          this.versions[sysname].legendData['gridData'][currentGridPath][
            'width'
          ]
    }
    // When switching between static and selectable legend.
    else {
      if (prevLegendType == 'static') {
        transitionWidthA =
          transitionWidthB =
          transitionWidthC =
            this.versions[old_sysname].legendData['gridData'][currentGridPath][
              'width'
            ]
      } else {
        transitionWidthA =
          this.versions[old_sysname].legendData.gridData.gridA.width
        transitionWidthB =
          this.versions[old_sysname].legendData.gridData.gridB.width
        transitionWidthC =
          this.versions[old_sysname].legendData.gridData.gridC.width
      }
    }

    // Create child nodes of SVG element.
    const legendSquareC = legendSVG
      .append('rect')
      .attr('id', legendSVGID + 'C')
      .attr('x', '20') // Padding of 20px on the left
      .attr('y', '5')
      .attr('fill', '#eeeeee')
      .attr('stroke', '#AAAAAA')
      .attr('stroke-width', '2px')

    const legendSquareB = legendSVG
      .append('rect')
      .attr('id', legendSVGID + 'B')
      .attr('x', '20') // Padding of 20px on the left
      .attr('y', '5')
      .attr('fill', '#EEEEEE')
      .attr('stroke', '#AAAAAA')
      .attr('stroke-width', '2px')

    const legendSquareA = legendSVG
      .append('rect')
      .attr('id', legendSVGID + 'A')
      .attr('x', '20') // Padding of 20px on the left
      .attr('y', '5')
      .attr('fill', '#FFFFFF')
      .attr('stroke', '#AAAAAA')
      .attr('stroke-width', '2px')

    const legendText = legendSVG
      .append('text')
      .attr('id', 'legend-text')
      .attr('fill', '#5A5A5A')
      .attr('dy', '0.3em') // vertical alignment

    // Adjust width of square according to chosen nice number and add transition to Legends
    legendSquareA
      .attr('width', transitionWidthA)
      .attr('height', transitionWidthA)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', widthA)
      .attr('height', widthA)

    legendSquareB
      .attr('width', transitionWidthB)
      .attr('height', transitionWidthB)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', widthB)
      .attr('height', widthB)

    legendSquareC
      .attr('width', transitionWidthC)
      .attr('height', transitionWidthC)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', widthC)
      .attr('height', widthC)

    // Set "x" and "y" of legend text relative to square's width
    legendText
      .attr('x', (20 + widthC + 15).toString() + 'px')
      .attr('y', (5 + widthC * 0.5).toString() + 'px')
      .attr('opacity', 0)

    // Set legend text
    legendText.append('tspan').html(' &#xD7; ')

    legendText
      .append('tspan')
      .attr('id', legendSVGID + '-multiplier')
      .text('10000')

    legendText.append('tspan').text(' = ')

    legendText
      .append('tspan')
      .attr('id', legendSVGID + '-number')
      .attr('font-weight', 'bold')
      .text('9999')

    legendText
      .append('tspan')
      .attr('id', legendSVGID + '-unit')
      .attr('font-weight', 'bold')
      .text(' placeholder')

    const largeNumberNames = { 6: ' million', 9: ' billion' }

    if (scalePowerOf10 > -4 && scalePowerOf10 < 12) {
      if (scalePowerOf10 in largeNumberNames) {
        // legendText.text("= " + scaleNiceNumberA + " " + largeNumberNames[scalePowerOf10] + " " + unit);
        d3.select('#' + legendSVGID + '-number').text(scaleNiceNumberA)
        d3.select('#' + legendSVGID + '-unit').text(
          ' ' + largeNumberNames[scalePowerOf10] + ' ' + unit
        )
      } else if (scalePowerOf10 > 9) {
        // legendText.text("= " + (scaleNiceNumberA * Math.pow(10, scalePowerOf10-9) + " billion " + unit));
        d3.select('#' + legendSVGID + '-number').text(
          scaleNiceNumberA * Math.pow(10, scalePowerOf10 - 9)
        )
        d3.select('#' + legendSVGID + '-unit').text(' billion ' + unit)
      } else if (scalePowerOf10 > 6) {
        // legendText.text("= " + (scaleNiceNumberA * Math.pow(10, scalePowerOf10-6) + " million " + unit));
        d3.select('#' + legendSVGID + '-number').text(
          scaleNiceNumberA * Math.pow(10, scalePowerOf10 - 6)
        )
        d3.select('#' + legendSVGID + '-unit').text(' million ' + unit)
      } else {
        d3.select('#' + legendSVGID + '-number').text(
          (scaleNiceNumberA * Math.pow(10, scalePowerOf10))
            .toLocaleString()
            .split(',')
            .join(' ')
        )
        d3.select('#' + legendSVGID + '-unit').text(' ' + unit)
      }

      // Adjust multiplier
      d3.select('#' + legendSVGID + '-multiplier').text(
        Math.pow(10, scalePowerOf10).toLocaleString().split(',').join(' ')
      )
    }
    // If scalePowerOf10 is too extreme, we use scientific notation
    else {
      d3.select('#' + legendSVGID + '-number').text(scaleNiceNumberA)
      d3.select('#' + legendSVGID + '-unit').html(' &#xD7; 10')
      legendText
        .append('tspan')
        .text(scalePowerOf10)
        .style('font-size', '10px')
        .attr('dy', '-10px')
      legendText.append('tspan').text(unit).attr('dy', '10px').attr('dx', '8px')
    }

    // Event for when a different legend size is selected.
    const legendNumber = d3.select('#' + legendSVGID + '-number').text()

    const changeToC = () => {
      // Update currentGridPath in SVG Data
      document.getElementById(legendSVGID).dataset.currentGridPath = 'gridC'

      d3.select('#' + legendSVGID + 'C').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')

      d3.select('#' + legendSVGID.substring(0, legendSVGID.length - 6) + 'grid')
        .transition()
        .duration(1000)
        .attr('d', gridC)

      d3.select('#' + legendSVGID + '-number').text(
        parseInt(
          (parseInt(legendNumber.substring(0, 1)) / scaleNiceNumberA) *
            scaleNiceNumberC +
            legendNumber.substring(1, legendNumber.length).split(' ').join('')
        )
          .toLocaleString()
          .split(',')
          .join(' ')
      )
    }

    const changeToB = () => {
      // Update currentGridPath in SVG Data
      document.getElementById(legendSVGID).dataset.currentGridPath = 'gridB'

      d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')

      d3.select('#' + legendSVGID.substring(0, legendSVGID.length - 6) + 'grid')
        .transition()
        .duration(1000)
        .attr('d', gridB)

      d3.select('#' + legendSVGID + '-number').text(
        parseInt(
          (parseInt(legendNumber.substring(0, 1)) / scaleNiceNumberA) *
            scaleNiceNumberB +
            legendNumber.substring(1, legendNumber.length).split(' ').join('')
        )
          .toLocaleString()
          .split(',')
          .join(' ')
      )
    }

    const changeToA = () => {
      // Update currentGridPath in SVG Data
      document.getElementById(legendSVGID).dataset.currentGridPath = 'gridA'

      d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')

      d3.select('#' + legendSVGID.substring(0, legendSVGID.length - 6) + 'grid')
        .transition()
        .duration(1000)
        .attr('d', gridA)

      d3.select('#' + legendSVGID + '-number').text(legendNumber)
    }

    //Update colors of the legend
    if (currentGridPath == 'gridA') {
      d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + '-number').text(legendNumber)
    } else if (currentGridPath == 'gridB') {
      d3.select('#' + legendSVGID + 'C').attr('fill', '#EEEEEE')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + '-number').text(
        (parseInt(legendNumber.substring(0, 1)) / scaleNiceNumberA) *
          scaleNiceNumberB +
          legendNumber.substring(1, legendNumber.length)
      )
    } else if (currentGridPath == 'gridC') {
      d3.select('#' + legendSVGID + 'C').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'B').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + 'A').attr('fill', '#FFFFFF')
      d3.select('#' + legendSVGID + '-number').text(
        (parseInt(legendNumber.substring(0, 1)) / scaleNiceNumberA) *
          scaleNiceNumberC +
          legendNumber.substring(1, legendNumber.length)
      )
    }

    legendSquareC.attr('cursor', 'pointer').on('click', changeToC)
    legendSquareB.attr('cursor', 'pointer').on('click', changeToB)
    legendSquareA.attr('curser', 'pointer').on('click', changeToA)

    // Add legend square labels
    const c_label = legendSVG
      .append('text')
      .attr('x', 20 + widthC - 13)
      .attr('y', widthC)
      .attr('font-size', 8)
      .attr('cursor', 'pointer')
      .text(scaleNiceNumberC)
      .attr('opacity', 0)
      .on('click', changeToC)

    let b_label_location_shift_x = 10
    let b_label_location_shift_y = 0
    // If there is less space between 'a' square and 'b' square, then we move the b label bit to the right and down
    if (widthB - widthA < 11) {
      b_label_location_shift_y = 2.3
      if (scaleNiceNumberB >= 10) {
        b_label_location_shift_x = 9
      } else {
        b_label_location_shift_x = 7
      }
    }

    const b_label = legendSVG
      .append('text')
      .attr('x', 20 + widthB - b_label_location_shift_x)
      .attr('y', widthB + b_label_location_shift_y)
      .attr('font-size', 8)
      .attr('cursor', 'pointer')
      .text(scaleNiceNumberB)
      .attr('opacity', 0)
      .on('click', changeToB)

    const a_label = legendSVG
      .append('text')
      .attr('x', 20 + widthA - 10)
      .attr('y', widthA)
      .attr('font-size', 8)
      .attr('cursor', 'pointer')
      .text(scaleNiceNumberA)
      .attr('opacity', 0)
      .on('click', changeToA)

    // Accommodate enough space so that even the resizable legend also fits in; it keeps the customise, download, share
    // buttons on place
    let legendSVGHeight = widthC
    Object.keys(this.versions).forEach(function (version_sysname) {
      legendSVGHeight = Math.max(
        legendSVGHeight,
        this.versions[version_sysname].legendData.gridData.gridC.width
      )
    }, this)

    // Adjust height of legendSVG
    legendSVG.attr('height', legendSVGHeight + 30)

    // Set "y" of total value text to be 20px below the top of the square.
    const totalValue = legendSVG
      .append('text')
      .attr('id', 'total-text')
      .attr('x', '20') // Padding of 20px on the left
      .attr('fill', '#5A5A5A')
      .attr('opacity', 0)

    const total_value_Y = 5 + parseInt(widthC) + 20
    totalValue.attr('y', total_value_Y.toString() + 'px')

    // Set total value text.
    const totalScalePowerOfTen = Math.floor(Math.log10(versionTotalValue))
    if (totalScalePowerOfTen > -4 && totalScalePowerOfTen < 12) {
      if (totalScalePowerOfTen in largeNumberNames)
        totalValue.text(
          'Total: ' +
            (
              versionTotalValue / Math.pow(10, totalScalePowerOfTen)
            ).toPrecision(3) +
            ' ' +
            largeNumberNames[totalScalePowerOfTen] +
            ' ' +
            unit
        )
      else if (totalScalePowerOfTen > 9)
        totalValue.text(
          'Total: ' +
            (versionTotalValue / Math.pow(10, 9)).toPrecision(3) +
            ' billion ' +
            unit
        )
      else if (totalScalePowerOfTen > 6)
        totalValue.text(
          'Total: ' +
            (versionTotalValue / Math.pow(10, 6)).toPrecision(3) +
            ' million ' +
            unit
        )
      // Else we display the total as it is
      else
        totalValue.text(
          'Total: ' +
            versionTotalValue.toLocaleString().split(',').join(' ') +
            ' ' +
            unit
        )
    }
    // If totalScalePowerOfTen is too extreme, we use scientific notation
    else {
      totalValue
        .append('tspan')
        .html(
          'Total : ' +
            (
              versionTotalValue / Math.pow(10, totalScalePowerOfTen)
            ).toPrecision(3) +
            ' &#xD7; 10'
        )
      totalValue
        .append('tspan')
        .text(totalScalePowerOfTen)
        .style('font-size', '10px')
        .attr('dy', '-10px')
      totalValue.append('tspan').text(unit).attr('dy', '10px').attr('dx', '8px')
    }

    // Add transition to Text elements
    c_label
      .transition()
      .ease(d3.easeCubic)
      .delay(200)
      .duration(800)
      .attr('opacity', 1)

    b_label
      .transition()
      .ease(d3.easeCubic)
      .delay(200)
      .duration(800)
      .attr('opacity', 1)

    a_label
      .transition()
      .ease(d3.easeCubic)
      .delay(200)
      .duration(800)
      .attr('opacity', 1)

    totalValue
      .transition()
      .ease(d3.easeCubic)
      .delay(300)
      .duration(700)
      .attr('opacity', 1)

    legendText
      .transition()
      .ease(d3.easeCubic)
      .delay(300)
      .duration(700)
      .attr('opacity', 1)

    // Verify if legend is accurate
    this.verifyLegend(
      sysname,
      widthA,
      scaleNiceNumberA * Math.pow(10, scalePowerOf10)
    )

    // Update Selected Legend Type in SVG Data
    document.getElementById(legendSVGID).dataset.legendType = 'resizable'
  }

  /**
   * getGridPath generates an SVG path for grid lines
   * @param {number} gridWidth
   * @param {number} width
   * @param {number} height
   */
  getGridPath(gridWidth, width, height) {
    let gridPath = ''

    // Vertical lines
    for (let i = 0; i < 30; i++) {
      gridPath +=
        'M' +
        (20 + gridWidth * i) +
        ' 0 L' +
        (20 + gridWidth * i) +
        ' ' +
        height +
        ' '
    }

    // Horizontal Lines
    for (let j = 1; j <= 30; j++) {
      gridPath +=
        'M0 ' +
        (height - gridWidth * j) +
        ' L' +
        width +
        ' ' +
        (height - gridWidth * j) +
        ' '
    }

    return gridPath
  }

  /**
   * drawGridLines appends grid lines to the map
   * @param {string} sysname A unique system identifier for the version
   * @param {string} mapSVGID The map's SVG element's ID
   * @param {string} old_sysname The previous sysname after map version switch. Optional.
   */
  drawGridLines(sysname, mapSVGID, old_sysname = null) {
    const currentGridPath = document.getElementById(mapSVGID + '-legend')
      .dataset.currentGridPath
    const gridPath =
      this.versions[sysname].legendData['gridData'][currentGridPath]['gridPath']
    const gridVisibility =
      document.getElementById(mapSVGID).dataset.gridVisibility

    const mapSVG = d3.select('#' + mapSVGID + '-svg')
    let gridSVGID = mapSVGID + '-grid'
    mapSVG.selectAll('#' + gridSVGID).remove() // Remove existing grid

    let stroke_opacity

    if (gridVisibility == 'off') {
      stroke_opacity = 0
    } else {
      stroke_opacity = 0.4
    }
    // The previous grid path from which we want to transition from
    let transitionGridPath = null

    if (old_sysname != null) {
      transitionGridPath =
        this.versions[old_sysname].legendData['gridData'][currentGridPath][
          'gridPath'
        ]
    }

    mapSVG
      .append('path')
      .attr('id', gridSVGID)
      .attr('stroke-opacity', stroke_opacity)
      .attr('d', transitionGridPath)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('d', gridPath)
      .attr('fill', 'none')
      .attr('stroke', '#5A5A5A')
      .attr('stroke-width', '2px')
  }

  /**
   * addVersion adds a new version to the map. If a version with the specified sysname already exists, it will be overwritten.
   * @param {string} sysname A unique system identifier for the version
   * @param {MapVersionData} data Data for the new map version.
   * @param {string} base_sysname Sysname of the version to be used as the standard for area equalization
   */
  addVersion(sysname, data, base_sysname) {
    if (this.versions.hasOwnProperty(sysname)) {
      delete this.versions[sysname]
    }

    // Here, the algorithm tries to equalize maps without distorting its initial width-height proportion. It uses the base version's
    // area as standard (currently, it is always the equal area map) and tries to make other map version's area (e.g population and cartogram map)
    // equal to that by scaling them  up or down as necessary.
    var scale_factors = {}
    var version_dimension = {}

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
      const base_version_geojson_area =
        this.getTotalAreasAndValuesForVersion(base_sysname)[0]
      const base_version_width_geojson =
        this.versions[base_sysname].extrema.max_x -
        this.versions[base_sysname].extrema.min_x
      const base_version_height_geojson =
        this.versions[base_sysname].extrema.max_y -
        this.versions[base_sysname].extrema.min_y
      const base_version_width =
        this.versions[base_sysname].dimension.x / this.config.scale
      const base_version_height =
        this.versions[base_sysname].dimension.y / this.config.scale
      const area_factor =
        (base_version_height_geojson / base_version_height) *
        (base_version_width_geojson / base_version_width)
      const base_version_area = base_version_geojson_area / area_factor

      // Calculate current sysname's GeoJSON area
      var version_total_area_geojson = 0
      Object.keys(data.regions).forEach(function (region_id) {
        let region = data.regions[region_id]

        let version_area_value_geojson = 0
        region.polygons.forEach(function (polygon) {
          const coordinates = polygon.coordinates

          version_area_value_geojson += Math.abs(d3.polygonArea(coordinates))

          polygon.holes.forEach(function (hole) {
            version_area_value_geojson -= Math.abs(d3.polygonArea(hole))
          }, this)
        }, this)
        version_total_area_geojson += version_area_value_geojson
      }, this)

      var version_area =
        version_total_area_geojson /
        ((version_width_geojson / version_width) *
          (version_height_geojson / version_height))
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

    Object.keys(data.regions).forEach(function (region_id) {
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
              (d) =>
                scale_factors[sysname].x * (-1 * data.extrema.min_x + d[0]),
              (d) => scale_factors[sysname].y * (data.extrema.max_y - d[1]),
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
  static highlightByID(where_drawn, region_id, color, highlight) {
    where_drawn.forEach(function (element_id) {
      var polygons = document.getElementsByClassName(
        'path-' + element_id + '-' + region_id
      )

      for (let i = 0; i < polygons.length; i++) {
        if (highlight) {
          polygons[i].setAttribute('fill', tinycolor(color).brighten(20))
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
  drawTooltip(event, region_id) {
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
  drawVersion(sysname, element_id, where_drawn) {
    var map_container = document.getElementById(element_id)
    var version = this.versions[sysname]
    var version_width = this.versions[sysname].dimension.x
    var version_height = this.versions[sysname].dimension.y

    // Empty the map container element
    while (map_container.firstChild) {
      map_container.removeChild(map_container.firstChild)
    }

    var canvas = d3
      .select('#' + element_id)
      .append('svg')
      .attr('id', element_id + '-svg')
      .attr('width', this.max_width)
      .attr('height', this.max_height)

    var polygons_to_draw = []

    // First we collect the information for each polygon to make using D3 easier.
    Object.keys(this.regions).forEach(function (region_id) {
      this.regions[region_id]
        .getVersion(sysname)
        .polygons.forEach(function (polygon) {
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

      if (p1.elevated && p2.elevated) {
        return 0
      }

      if (!p1.elevated && p2.elevated) {
        return -1
      }

      if (!p1.elevated && !p2.elevated) {
        return 0
      }
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
          (d.value === 'NA' ? '-na' : '')
      )
      /* NA regions are filled with white */
      .attr('fill', (d) => (d.value === 'NA' ? '#CCCCCC' : d.color))
      .attr('stroke', '#000')
      .attr('stroke-width', '0.5')
      .on(
        'mouseenter',
        (function (map, where_drawn) {
          return function (event, d, i) {
            CartMap.highlightByID(where_drawn, d.region_id, d.color, true)

            map.drawTooltip(event, d.region_id)
          }
        })(this, where_drawn)
      )
      .on(
        'mousemove',
        (function (map) {
          return function (event, d, i) {
            map.drawTooltip(event, d.region_id)
          }
        })(this)
      )
      .on(
        'mouseleave',
        (function (map, where_drawn) {
          return function (d, i) {
            CartMap.highlightByID(where_drawn, d.region_id, d.color, false)

            Tooltip.hide()
          }
        })(this, where_drawn)
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
        const x2LongLat = (x) => x / labels.scale_x + xMinLong
        const y2LongLat = (y) => yMaxLat - y / labels.scale_y

        // 2) longlat -> gall peters
        let project = new GallPetersProjection()
        const x2Gall = project.transformLongitude
        const y2Gall = project.transformLatitude

        // 3) gall peters -> inkscape svg
        const xMinGall = project.transformLongitude(-180)
        const yMaxGall = project.transformLatitude(90)
        const gallWidth = project.transformLongitude(180) - xMinGall
        const gallScale = 750 / gallWidth
        const x2Ink = (x) => (x - xMinGall) * gallScale
        const y2Ink = (y) => (yMaxGall - y) * gallScale

        // We define a pipe function to accumulate the transformations.
        const pipe =
          (...fns) =>
          (x) =>
            fns.reduce(
              (accumulator, currentFunction) => currentFunction(accumulator),
              x
            )

        const xPipeline = pipe(x2LongLat, x2Gall, x2Ink)
        const yPipeLine = pipe(y2LongLat, y2Gall, y2Ink)

        const scaleX =
          version_width /
          ((version.extrema.max_x - version.extrema.min_x) * gallScale)
        const scaleY =
          version_height /
          ((version.extrema.max_y - version.extrema.min_y) * gallScale)

        var text = canvas
          .selectAll('text')
          .data(labels.labels)
          .enter()
          .append('text')

        var textLabels = text
          .attr('x', (d) => xPipeline(d.x) * scaleX)
          .attr('y', (d) => yPipeLine(d.y) * scaleY)
          .attr('font-family', 'sans-serif')
          .attr('font-size', '9.5px')
          .attr('fill', '#000')
          .text((d) => d.text)

        var lines = canvas
          .selectAll('line')
          .data(labels.lines)
          .enter()
          .append('line')

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
          version_width /
          ((version.extrema.max_x - version.extrema.min_x) * labels.scale_x)
        var scale_y =
          version_height /
          ((version.extrema.max_y - version.extrema.min_y) * labels.scale_y)

        var text = canvas
          .selectAll('text')
          .data(labels.labels)
          .enter()
          .append('text')

        var textLabels = text
          .attr('x', (d) => d.x * scale_x)
          .attr('y', (d) => d.y * scale_y)
          .attr('font-family', 'sans-serif')
          .attr('font-size', '7.5px')
          .attr('fill', '#000')
          .text((d) => d.text)

        var lines = canvas
          .selectAll('line')
          .data(labels.lines)
          .enter()
          .append('line')

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

  /**
   * switchVersion switches the map version displayed in the element with the given ID with an animation.
   * @param {string} current_sysname The sysname of the currently displayed version
   * @param {string} new_sysname The sysname of the version to be displayed
   * @param {string} element_id The ID of the element containing the map
   */
  switchVersion(current_sysname, new_sysname, element_id) {
    Object.keys(this.regions).forEach(function (region_id) {
      var region = this.regions[region_id]

      this.regions[region_id].versions[current_sysname].polygons.forEach(
        function (polygon) {
          // const targetPath = this.regions[region_id].versions[new_sysname].polygons.find(poly => poly.id == polygon.id).path;
          // console.log(targetPath);

          d3.select('#path-' + element_id + '-' + polygon.id)
            .attr('d', polygon.path)
            .transition()
            .ease(d3.easeCubic)
            .duration(1000)
            .attr(
              'd',
              this.regions[region_id].versions[new_sysname].polygons.find(
                (poly) => poly.id == polygon.id
              ).path
            )
          // .attrTween('d', function() {
          //     return d3.interpolatePath(polygon.path, targetPath);
          // })

          /* Change the color and ensure correct highlighting behavior after animation
                 is complete
              */
          window.setTimeout(
            function () {
              if (
                this.regions[region_id].versions[new_sysname].value === 'NA'
              ) {
                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .setAttribute('fill', '#cccccc')

                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .classList.remove('path-' + element_id + '-' + region_id)
                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .classList.add('path-' + element_id + '-' + region_id + '-na')
              } else {
                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .setAttribute('fill', this.colors[region_id])
                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .classList.add('path-' + element_id + '-' + region_id)
                document
                  .getElementById('path-' + element_id + '-' + polygon.id)
                  .classList.remove(
                    'path-' + element_id + '-' + region_id + '-na'
                  )
              }
            }.bind(this),
            800
          )
        },
        this
      )
    }, this)

    let selectedLegendType = document.getElementById(element_id + '-legend')
      .dataset.legendType

    if (selectedLegendType == 'static') {
      this.drawLegend(new_sysname, element_id + '-legend', current_sysname)
    } else {
      this.drawResizableLegend(
        new_sysname,
        element_id + '-legend',
        current_sysname
      )
    }

    this.drawGridLines(new_sysname, element_id, current_sysname)
  }
}
