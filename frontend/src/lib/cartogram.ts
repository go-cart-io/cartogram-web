/**
 * @fileOverview This file contains the frontend UI for the go-cart.io web application
 * @author Ian Duncan, Atima Tharatipyakul
 * @version 3.0.0
 */

import * as d3 from 'd3'
// import * as XLSX from 'xlsx/xlsx.mjs'

import HTTP from './http.js'
import { MapVersionData, MapDataFormat } from './mapVersion.js'
import CartMap from './cartMap.js'
import * as util from './util.js'
import type { Mappack } from './interface.js'

/**
 * Cartogram contains the main frontend logic for the go-cart web application.
 */
export default class Cartogram {
  cartogram_data_dir: string
  scale: number

  /**
   * The cartogram model
   * @property {CartMap|null} map The current map
   * @property {string} current_sysname The sysname of the map version selected for viewing on the right
   * @property {string} map_sysname The sysname of the currently selected map
   * @property {boolean} in_loading_state Whether or not we're in a loading state
   * @property {Object|null} loading_state The current loading state
   */
  model = {
    map: null as CartMap | null,
    current_sysname: '',
    map_sysname: '',
    in_loading_state: false,
    loading_state: null as Object | null
  }

  constructor(c_d: string, scale = 1.3) {
    this.cartogram_data_dir = c_d
    this.scale = scale
  }

  /**
   * downloadTemplateFile allows download of both CSV and Excel files
   * @param {string} sysname The sysname of the new version to be displayed
   */
  // async downloadTemplateFile(sysname: string) {
  //   if (!document.getElementById('csv-template-link')) return

  //   let templateLinkEl = document.getElementById('csv-template-link')! as HTMLAnchorElement
  //   templateLinkEl.href = this.cartogram_data_dir + '/' + sysname + '/template.csv'
  //   templateLinkEl.download = sysname + '_template.csv'
  //   var csv_file_promise = HTTP.get(
  //     this.cartogram_data_dir + '/' + sysname + '/template.csv',
  //     null,
  //     null,
  //     false
  //   )
  //   var csv_file = await csv_file_promise.then(function (response) {
  //     return response
  //   })

  //   // convert the csv file to json for easy convertion to excel file
  //   var lines = csv_file.split('\n')
  //   var json_file = []
  //   var headers = lines[0].split(',')
  //   for (var i = 1; i < lines.length - 1; i++) {
  //     var obj = {}
  //     var currentline = lines[i].split(',')
  //     for (var j = 0; j < headers.length; j++) {
  //       obj[headers[j]] = currentline[j]
  //     }
  //     json_file.push(obj)
  //   }

  //   // convert the json_file to excel file
  //   const fileName = sysname + '_template.xlsx'
  //   const ws = XLSX.utils.json_to_sheet(json_file)
  //   const wb = XLSX.utils.book_new()
  //   XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  //   document.getElementById('xlsx-template-link').onclick = function () {
  //     XLSX.writeFile(wb, fileName)
  //   }
  // }

  /**
   * displayCustomisePopup displays the customise popup on click on the customise button and controls the functionality of the checkboxes
   * @param {string} sysname The sysname of the new version to be displayed
   */

  displayCustomisePopup(sysname: string) {
    if (!this.model.map) return

    // Toggle the display of customise popup
    d3.select('#map-customise').on('click', function () {
      let element = document.getElementById('map-customise-popup')!
      let style = window.getComputedStyle(element)
      let display = style.getPropertyValue('display')
      if (display == 'block') {
        document.getElementById('map-customise-popup')!.style.display = 'none'
        document.getElementById('map-customise')!.style.backgroundColor = '#d76126'
        document.getElementById('map-customise')!.style.borderColor = '#d76126'
      } else if (display === 'none') {
        document.getElementById('map-customise-popup')!.style.display = 'block'
        document.getElementById('map-customise')!.style.backgroundColor = '#b75220'
        document.getElementById('map-customise')!.style.borderColor = '#ab4e1f'
      }
    })

    d3.select('#cartogram-customise').on('click', function () {
      let element = document.getElementById('cartogram-customise-popup')!
      let style = window.getComputedStyle(element)
      let display = style.getPropertyValue('display')
      if (display == 'block') {
        document.getElementById('cartogram-customise-popup')!.style.display = 'none'
        document.getElementById('cartogram-customise')!.style.backgroundColor = '#d76126'
        document.getElementById('cartogram-customise')!.style.borderColor = '#d76126'
      } else if (display === 'none') {
        document.getElementById('cartogram-customise-popup')!.style.display = 'block'
        document.getElementById('cartogram-customise')!.style.backgroundColor = '#b75220'
        document.getElementById('cartogram-customise')!.style.borderColor = '#ab4e1f'
      }
    })

    // Toggle the gridline visibility

    d3.select('#gridline-toggle-map').on('change', function () {
      if (d3.select('#gridline-toggle-map').property('checked')) {
        d3.select('#map-area-grid')
          .transition()
          .ease(d3.easeCubic)
          .duration(500)
          .attr('stroke-opacity', 0.4)
        document.getElementById('map-area')!.dataset.gridVisibility = 'on'
      } else {
        d3.select('#map-area-grid')
          .transition()
          .ease(d3.easeCubic)
          .duration(500)
          .attr('stroke-opacity', 0)
        document.getElementById('map-area')!.dataset.gridVisibility = 'off'
      }
    })

    d3.select('#gridline-toggle-cartogram').on('change', function () {
      if (d3.select('#gridline-toggle-cartogram').property('checked')) {
        d3.select('#cartogram-area-grid')
          .transition()
          .ease(d3.easeCubic)
          .duration(500)
          .attr('stroke-opacity', 0.4)
        document.getElementById('cartogram-area')!.dataset.gridVisibility = 'on'
      } else {
        d3.select('#cartogram-area-grid')
          .transition()
          .ease(d3.easeCubic)
          .duration(500)
          .attr('stroke-opacity', 0)
        document.getElementById('cartogram-area')!.dataset.gridVisibility = 'off'
      }
    })

    // Toggle legend between static and resizable

    d3.select('#legend-toggle-cartogram').on('change', () => {
      if (d3.select('#legend-toggle-cartogram').property('checked')) {
        this.model.map!.drawResizableLegend(sysname, 'cartogram-area-legend')
      } else {
        this.model.map!.drawLegend(sysname, 'cartogram-area-legend')
      }
    })

    d3.select('#legend-toggle-map').on('change', () => {
      if (d3.select('#legend-toggle-map').property('checked')) {
        this.model.map!.drawResizableLegend('1-conventional', 'map-area-legend')
      } else {
        this.model.map!.drawLegend('1-conventional', 'map-area-legend')
      }
    })
  }
  /**
   * requestAndDrawCartogram generates and displays a cartogram with a user-provided dataset. Always returns false to
   * prevent form submission.
   *
   * This is a two step process. First, we make a request to CartogramUI. This generates color and tooltip information
   * from the uploaded dataset, as well as the areas string that needs to be given to the cartogram generator to
   * actually generate the cartogram with the given dataset.
   *
   * Once it receives the areas string, the cartogram generator produces a streaming HTTP response with information on
   * the progress of cartogram generation, and the cartogram points in JSON format. The information from CartogramUI
   * and the cartogram generator is then combined to draw the cartogram with the correct colors and tooltip
   * information.
   * @param {Object} gd The grid document to retrieve the dataset from. If null, the dataset is taken from the
   * uploaded CSV file
   * @param {string} sysname The sysname of the map. If null, it is taken from the map selection form control.
   * @param {boolean} update_grid_document Wether to update the grid document with the grid document returned from
   * CartogramUI
   * @returns {boolean}
   */
  // async requestAndDrawCartogram(gd = null, sysname = null, update_grid_document = true) {
  //   if (this.model.in_loading_state) return false

  //   this.clearNonFatalError()

  //   /* Do some validation */

  //   if (gd === null && document.getElementById('csv').files.length < 1) {
  //     this.doNonFatalError(Error('You must upload CSV/Excel data.'))
  //     return false
  //   }

  //   // We check if the xlsx to csv conversion is ready; if not, we wait until it is
  //   this.enterLoadingState()
  //   this.showProgressBar()

  //   if (sysname === null) {
  //     sysname = document.getElementById('handler').value
  //   }

  //   var cartogramui_promise

  //   /*
  //       If we're submitting a grid document, convert it and pretend to upload a CSV file. Otherwise, actually upload the
  //       CSV file the user specified.
  //       */

  //   if (gd === null) {
  //     // Moved to UploadBtn
  //   } else {
  //     var cartogramui_req_body = this.generateCartogramUIRequestBodyFromGridDocument(sysname, gd)

  //     cartogramui_promise = HTTP.post(this.config.cartogramui_url, cartogramui_req_body.req_body, {
  //       'Content-Type': 'multipart/form-data; boundary=' + cartogramui_req_body.mime_boundary
  //     })
  //   }

  //   cartogramui_promise.then(
  //     function (response) {
  //       if (response.error == 'none') {
  //         // moved to c

  //         const yesButton = document.createElement('button')
  //         yesButton.className = 'btn btn-primary mr-5'
  //         yesButton.innerText = 'Yes, I Confirm'
  //         yesButton.addEventListener(
  //           'click',
  //           function (sysname, response) {
  //             return function (e) {

  //                 }.bind(this),
  //                 function (err) {
  //                   this.doFatalError(err)
  //                   console.log(err)

  //                   this.drawBarChartFromTooltip('barchart', response.tooltip)
  //                   document.getElementById('barchart-container').style.display = 'block'
  //                 }.bind(this)
  //               )
  //             }.bind(this)
  //           }.bind(this)(sysname, response)
  //         )

  //         pieChartButtonsContainer.appendChild(yesButton)
  //         pieChartButtonsContainer.appendChild(noButton)

  //         this.drawPieChartFromTooltip('piechart-area', response.tooltip, colors)
  //         this.exitLoadingState()
  //         document.getElementById('piechart').style.display = 'block'
  //       } else {
  //         this.exitLoadingState()
  //         document.getElementById('cartogram').style.display = 'block'
  //         this.doNonFatalError(Error(response.error))
  //       }
  //     }.bind(this),
  //     this.doFatalError
  //   )

  //   return false
  // }

  /**
   * switchMap loads a new map with the given sysname, and displays the conventional and population versions, as well
   * as an optional extra cartogram.
   * @param {string} sysname The sysname of the new map to load
   * @param {string} hrname The human-readable name of the new map to load
   * @param mappack
   * @param {MapVersionData} cartogram An optional, extra cartogram to display
   * @param {string} sharing_key The unique sharing key associated with this
   *                             cartogram, if any
   */
  switchMap(
    sysname: string,
    hrname: string,
    mappack: Mappack,
    cartogram: MapVersionData | null = null,
    sharing_key: string | null = null
  ) {
    var map = new CartMap(hrname, mappack.config, this.scale)

    /* We check if the map is a world map by searching for the 'extent' key in mappack.original.
               We then pass a boolean to the MapVersionData constructor.
             */
    let world = false
    if ('extent' in mappack.original) {
      world = mappack.original.extent === 'world'
    }

    /* We need to find out the map format. If the extrema is located in the bbox property, then we have
               GeoJSON. Otherwise, we have the old JSON format.
            */

    if (mappack.original.hasOwnProperty('bbox')) {
      var extrema = {
        min_x: mappack.original.bbox[0],
        min_y: mappack.original.bbox[1],
        max_x: mappack.original.bbox[2],
        max_y: mappack.original.bbox[3]
      }

      map.addVersion(
        '1-conventional',
        new MapVersionData(
          mappack.original.features,
          extrema,
          mappack.original.tooltip,
          mappack.abbreviations,
          mappack.labels,
          MapDataFormat.GEOJSON,
          world
        ),
        '1-conventional'
      )
    } else {
      map.addVersion(
        '1-conventional',
        new MapVersionData(
          mappack.original.features,
          mappack.original.extrema,
          mappack.original.tooltip,
          mappack.abbreviations,
          mappack.labels,
          MapDataFormat.GOCARTJSON,
          world
        ),
        '1-conventional'
      )
    }

    if (mappack.population.hasOwnProperty('bbox')) {
      var extrema = {
        min_x: mappack.population.bbox[0],
        min_y: mappack.population.bbox[1],
        max_x: mappack.population.bbox[2],
        max_y: mappack.population.bbox[3]
      }

      map.addVersion(
        '2-population',
        new MapVersionData(
          mappack.population.features,
          extrema,
          mappack.population.tooltip,
          null,
          null,
          MapDataFormat.GEOJSON,
          world
        ),
        '1-conventional'
      )
    } else {
      map.addVersion(
        '2-population',
        new MapVersionData(
          mappack.population.features,
          mappack.population.extrema,
          mappack.population.tooltip,
          null,
          null,
          MapDataFormat.GOCARTJSON,
          world
        ),
        '1-conventional'
      )
    }

    if (cartogram !== null) {
      map.addVersion('3-cartogram', cartogram, '1-conventional')
    }

    /*
            The keys in the colors.json file are prefixed with id_. We iterate through the regions and extract the color
            information from colors.json to produce a color map where the IDs are plain region IDs, as required by
            CartMap.
            */
    var colors: { [key: string]: string } = {}

    Object.keys(map.regions).forEach(function (region_id) {
      colors[region_id] = mappack.colors['id_' + region_id]
    }, this)

    map.colors = colors

    map.drawVersion('1-conventional', 'map-area', ['map-area', 'cartogram-area'])

    if (cartogram !== null) {
      map.drawVersion('3-cartogram', 'cartogram-area', ['map-area', 'cartogram-area'])
      this.model.current_sysname = '3-cartogram'
    } else {
      map.drawVersion('2-population', 'cartogram-area', ['map-area', 'cartogram-area'])
      this.model.current_sysname = '2-population'
    }

    this.model.map = map

    // this.downloadTemplateFile(sysname)
    this.displayCustomisePopup(this.model.current_sysname)

    let selectedLegendTypeMap = document.getElementById('map-area-legend')!.dataset.legendType
    let selectedLegendTypeCartogram =
      document.getElementById('cartogram-area-legend')!.dataset.legendType

    if (selectedLegendTypeMap == 'static') {
      this.model.map.drawLegend('1-conventional', 'map-area-legend', null, true)
    } else {
      this.model.map.drawResizableLegend('1-conventional', 'map-area-legend')
    }

    if (selectedLegendTypeCartogram == 'static') {
      this.model.map.drawLegend(this.model.current_sysname, 'cartogram-area-legend', null, true)
    } else {
      this.model.map.drawResizableLegend(this.model.current_sysname, 'cartogram-area-legend')
    }

    // The following line draws the conventional legend when the page first loads.
    this.model.map.drawGridLines('1-conventional', 'map-area')
    this.model.map.drawGridLines(this.model.current_sysname, 'cartogram-area')

    document.getElementById('cartogram')!.style.display = 'block'
  }
}
