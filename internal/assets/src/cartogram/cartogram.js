/**
 * @fileOverview This file contains the frontend UI for the go-cart.io web application
 * @author Ian Duncan, Atima Tharatipyakul
 * @version 2.0.0
 */

import * as d3 from "d3";
import tinycolor from "tinycolor2";
import * as XLSX from 'xlsx/xlsx.mjs';

import HTTP from './http.js'
import Tooltip from './tooltip.js'
import { MapVersionData, MapDataFormat } from './mapVersion.js'
import CartMap from './cartMap.js'
import * as util from './util.js';
window.util = util;

 /**
  * Extrema for a map
  * @typedef {Object} Extrema
  * @property {number} min_x
  * @property {number} max_x
  * @property {number} min_y
  * @property {number} max_y
  */

/**
 * Configuration for a map. Some maps do not display properly without modification. This configuration information
 * allows us to draw maps properly by hiding certain polygons, and changing the order in which they are drawn.
 * @typedef {Object} MapConfig
 * @property {Array} dont_draw A list of polygon IDs not to draw
 * @property {Array} elevate A list of polygon IDs to draw after all others
 */

/**
 * Labels for a map version
 * @typedef {Object} Labels
 * @property {number} scale_x Horizontal scaling factor for all label coordinates
 * @property {number} scale_y Vertical scaling factor for all label coordinates
 * @property {Array<{x: number, y: number, text: string}>} labels Text labels
 * @property {Array<{x1: number, y1: number, x2: number, y2: number}>} lines Line labels
 */

/**
 * Cartogram contains the main frontend logic for the go-cart web application.
 */
export class Cartogram {

    /**
     * constructor creates an instance of the Cartogram class
     * @param {string} c_u The URL of the cartogram generator
     * @param {string} cui_u The cartogramui URL
     * @param {string} c_d  The URL of the cartogram data directory
     * @param {string} g_u The URL of the gridedit page
     * @param {string} gp_u The URL to retrieve progress information
     * @param {string} version The version string used to prevent improper caching of map assets
     */

    constructor(c_u, cui_u, c_d, g_u, gp_u, version, scale=1.3) {

        this.config = {
            cartogram_url: c_u,
            cartogramui_url: cui_u,
            cartogram_data_dir: c_d,
            gridedit_url: g_u,
            getprogress_url: gp_u,
            version: version,
	    scale: scale,
        };

        /**
         * The cartogram model
         * @property {CartMap|null} map The current map
         * @property {string} current_sysname The sysname of the map version selected for viewing on the right
         * @property {string} map_sysname The sysname of the currently selected map
         * @property {boolean} in_loading_state Whether or not we're in a loading state
         * @property {Object|null} loading_state The current loading state
         * @property {Object|null} grid_document The current grid document
         * @property {Window|null} gridedit_window The {@link Window} of the gridedit interface
         */
        this.model = {
            map: null,
            current_sysname: '',
            map_sysname: '',
            in_loading_state: false,
            loading_state: null,
            grid_document: null,
            gridedit_window: null,
        };

        /**
         * Contains extended information about a fatal error. Used to produce a meaningful error report when cartogram
         * generation fails
         * @type {string|null}
         */
        this.extended_error_info = null;

        // Close the gridedit window upon navigating away from the page if it's open
        window.onbeforeunload = function() {
            if(this.model.gridedit_window !== null && !this.model.gridedit_window.closed)
            {
                this.model.gridedit_window.close();
            }
        }.bind(this);

    }

    /**
     * setExtendedErrorInfo sets the extended error information. You must call this function before doFatalError to
     * display this information.
     * @param {string} info The extended error information, in plaintext
     */
    setExtendedErrorInfo(info) {

        this.extended_error_info = info;

    }

    /**
     * appendToExtendedErrorInfo appends new text to the existing extended error information.
     * @param {string} info The additional extended error information, in plaintext
     */
    appendToExtendedErrorInfo(info) {

        this.extended_error_info += info;

    }

    /**
     * clearExtendedErrorInfo clears the existing extended error information.
     */
    clearExtendedErrorInfo() {

        this.extended_error_info = null;

    }

    /**
     * launchGridEdit opens the gridedit window if possible.
     */
    launchGridEdit() {

        if(this.model.grid_document === null || this.model.in_loading_state)
            return;

        if(this.model.gridedit_window === null || this.model.gridedit_window.closed)
        {
            this.model.gridedit_window = window.open(this.config.gridedit_url, "gridedit_" + new Date().getTime(), 'width=550,height=650,resizable,scrollbars');

            this.model.gridedit_window.addEventListener("load", (function(gd){

                return function(e) {
                    this.model.gridedit_window.gridedit_init();

                    this.model.gridedit_window.gridedit.on_update = function(gd) {

                        this.onGridEditUpdate(gd);

                    }.bind(this);

                    /*
                    This sets whether or not the Update button is clickable in the gridedit document
                    */
                    this.model.gridedit_window.gridedit.set_allow_update(!this.model.in_loading_state);

                    this.model.gridedit_window.gridedit.load_document(gd);
                }.bind(this);

            }.bind(this)(this.model.grid_document)));
        }
        else
        {
            this.model.gridedit_window.gridedit.load_document(this.model.grid_document);
            this.model.gridedit_window.focus();
        }

    }

    /**
     * onGridEditUpdate generates and displays a cartogram using the dataset in the current grid document when the
     * update button is clicked in the gridedit interface.
     * @param {Object} gd The updated grid document
     */
    onGridEditUpdate(gd) {

        if(this.model.in_loading_state)
            return;

        /*
        The user may make changes to the grid document while the cartogram loads. As a result, we don't want to update
        the grid document with the one returned by CartogramUI.
        */
        this.requestAndDrawCartogram(gd, null, false);

    }

    /**
     * editButtonDisabled returns whether the edit button to launch the gridedit window should be disabled.
     * @returns {boolean}
     */
    editButtonDisabled() {
        return this.grid_document === null;
    }

    /**
     * updateGridDocument updates the current grid document.
     * @param {Object} new_gd The new grid document
     */
    updateGridDocument(new_gd) {

        this.model.grid_document = new_gd;

        if(this.model.grid_document !== null)
        {
            if(!this.model.in_loading_state)
                document.getElementById('edit-button').disabled = false;

            /*
            If the gridedit window is open, push the new grid document to it
            */
            if(this.model.gridedit_window !== null && !this.model.gridedit_window.closed)
                this.model.gridedit_window.gridedit.load_document(this.model.grid_document);
        }
        else
        {
            document.getElementById('edit-button').disabled = true;
        }

    }

    /**
     * gridDocumentToCSV takes a grid document and converts it to CSV format with Excel-style quote escaping.
     * @param {Object} gd The grid document to convert
     */
    gridDocumentToCSV(gd) {

        var csv = "";

        for(let row = 0; row < gd.height; row++)
        {
            for(let col = 0; col < gd.width; col++)
            {
                /*
                We use Excel-style quote escaping. All values are placed within double quotes, and a double quote
                literal is represented by "".
                */
                csv += '"' + gd.contents[(row * gd.width) + col].replace(/"/gm, '""') + '"';

                if(col < (gd.width - 1))
                {
                    csv += ",";
                }
            }

            if(row < (gd.height - 1))
            {
                csv += "\n";
            }
        }

        return csv;

    }

    /**
     * @typedef {Object} RequestBody An HTTP POST multipart request body
     * @property {string} mime_boundary The MIME boundary for the request, which must be sent as a header
     * @property {string} req_body The request body text
     */

    /**
     * generateCartogramUIRequestBodyFromGridDocument generates a POST request body for CartogramUI from a grid
     * document. To do this, we convert the grid document to CSV format and pretend we're uploading it as a file. This
     * simplifies the backend code.
     * @param {string} sysname The sysname of the map.
     * @param {Object} gd The grid document
     * @returns {RequestBody}
     */
    generateCartogramUIRequestBodyFromGridDocument(sysname, gd) {

        var mime_boundary = HTTP.generateMIMEBoundary();
        var csv = this.gridDocumentToCSV(gd);

        // The MIME boundary can't be contained in the request body text
        while(true)
        {
            var search_string = csv + "csv" + "handler" + handler;
            if(search_string.search(mime_boundary) === -1)
                break;

            mime_boundary = HTTP.generateMIMEBoundary();
        }

        var req_body = "";

        req_body += "--" + mime_boundary + "\n";
        req_body += 'Content-Disposition: form-data; name="handler"\n\n'
        req_body += sysname + "\n";

        req_body += "--" + mime_boundary + "\n";
        req_body += 'Content-Disposition: form-data; name="csv"; filename="data.csv"\n';
        req_body += 'Content-Type: text/csv\n\n';
        req_body += csv + "\n";
        req_body += "--" + mime_boundary + "--";

        return {
            mime_boundary: mime_boundary,
            req_body: req_body
        };

    }

    /**
     * drawChartFromTooltip draws a barchart of the uploaded dataset, which can be found in the tooltip of the
     * CartogramUI response. We use this when CartogramUI returns a success response, but cartogram generation fails.
     * @param {string} container The ID of the element to draw the barchart in
     * @param {Object} tooltip The tooltip to retrieve the data from
     */
    drawBarChartFromTooltip(container, tooltip) {

        var margin = {top: 5, right: 5, bottom: 5, left: 50},
        width = 800 - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

        // ranges
        var x = d3.scaleBand()
                  .rangeRound([0, width])
                  .padding(0.05);

        var y = d3.scaleLinear().range([height, 0]);

        // axes
        var xAxis = d3.axisBottom(x);

        var yAxis = d3.axisLeft(y)
                      .ticks(10);

        // SVG element
        var svg = d3.select("#" + container).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

        // Data formatting
        var data = new Array();

        Object.keys(tooltip.data).forEach(function(key, index){

            data.push(tooltip.data[key]);

        });

        /* Display in alphabetical order */
        data.sort(function(a,b){

            if(a.name<b.name)
                return -1;
            else if(a.name>b.name)
                return 1;
            else
                return 0;

        });

        // scale the range of the data
        x.domain(data.map(function(d) { return d.name; }));
        y.domain([0, d3.max(data, function(d) { return d.value; }) + 5]);

        // add axes
        svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", "-.55em")
        .attr("transform", "rotate(-90)" );

        svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 5)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("User Data");

        // add the bar chart
        svg.selectAll("bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", function(d) { return x(d.name); })
        .attr("width", x.bandwidth())
        .attr("y", function(d) { return y(d.value); })
        .attr("height", function(d) { return height - y(d.value); });

    }

    drawPieChartFromTooltip(container, tooltip, colors) {

        const containerElement = document.getElementById(container);

        while(containerElement.firstChild) {
            containerElement.removeChild(containerElement.firstChild);
        }

        const svg = d3.select('#' + container).append('svg').append('g');

        svg.append("g")
            .attr("class", "slices");
        svg.append("g")
            .attr("class", "labels");
        svg.append("g")
            .attr("class", "lines");

        const width = 600,
            height = 450,
            radius = Math.min(width, height) / 2;

        const pie = d3.pie()
            .sort(null)
            .value(d => d.value);

        const arc = d3.arc()
            .outerRadius(radius * 0.8)
            .innerRadius(0);

        const outerArc = d3.arc()
            .innerRadius(radius * 0.9)
            .outerRadius(radius * 0.9);

        svg.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

        const key = d => d.data.label;

        const dataWithOthers = Object.keys(this.model.map.regions).map((region_id, _i, _a) => {
            return {
                label: region_id,
                value: tooltip.data["id_" + region_id].value,
                color: colors[region_id],
                abbreviation: this.model.map.regions[region_id].abbreviation,
                name: this.model.map.regions[region_id].name
            };
        }, this).filter(d => d.value !== "NA");

        const formatAsScientificNotation = (num) => {

            const rounded = num.toPrecision(4);
            const parts = rounded.split("e");

            if(parts.length === 2) {
                return `${parts[0]}&nbsp;&times;&nbsp;10<sup>${parts[1].replace("+", "")}</sup>`
            } else {
                return rounded;
            }

        };

        const total = dataWithOthers.reduce((acc, datum) => acc + datum.value, 0);
        document.getElementById('data-total').innerHTML = formatAsScientificNotation(total) + (tooltip.unit === "" ? "" : " " + tooltip.unit);

        const othersThreshold = total*0.025;

        let others = {
            label: "_others",
            value: 0,
            color: "#aaaaaa",
            abbreviation: "Others",
            name: "Others"
        };

        dataWithOthers.forEach((datum) => {

            if(datum.value < othersThreshold) {

                others.value += datum.value;

            }

        });

        let data = dataWithOthers;

        if(others.value > 0) {

            data = dataWithOthers.filter(d => d.value >= othersThreshold);
            data.push(others);

        }

        // Reorder the data to reduce neighboring regions having the same color

        for(let i = 0; i < data.length; i++) {

            // If the (i + 1)th has the same color as ith slice...
            if(data[i].color === data[(i + 1) % data.length].color) {

                // Try to find a slice *different* color, such that swapping it won't result in neighboring slices
                // having the same color.
                // If we find one, swap it with the (i + 1)th slice.
                for(let j = i + 2; j < data.length + i + 2; j++) {

                    if (
                        data[j % data.length].color !== data[(i + 1) % data.length].color &&
                        data[(j + 1) % data.length].color !== data[(i + 1) % data.length].color &&
                        data[(j - 1) % data.length].color !== data[(i + 1) % data.length].color
                    ) {

                        const temp = data[j % data.length];
                        data[j % data.length] = data[(i + 1) % data.length];
                        data[(i + 1) % data.length] = temp;
                        break;

                    }

                }

            }

        }

        const totalValue = data.reduce((total, d, _i, _a) =>
            d.value !== "NA" ? total + d.value : total
            , 0);

        let slice = svg
            .select(".slices")
            .selectAll("path.slice")
            .data(pie(data));

        slice = slice.enter()
                     .insert("path")
                     .style("fill", d => d.data.color)
                     .attr("class", "slice")
                     .on("mouseover", function(event, d, i){

                         d3.select(this).style("fill", tinycolor(d.data.color).brighten(20));

                         Tooltip.drawWithEntries(
                             event,
                             d.data.name,
                             d.data.abbreviation,
                             [{
                                 name: tooltip.label,
                                 value: d.data.value,
                                 unit: tooltip.unit
                             }]
                         );
                     })
                     .on("mousemove", function(event, d, i){

                         Tooltip.drawWithEntries(
                             event,
                             d.data.name,
                             d.data.abbreviation,
                             [{
                                 name: tooltip.label,
                                 value: d.data.value,
                                 unit: tooltip.unit
                             }]
                         );
                     })
                     .on("mouseout", function(event, d, i){

                         d3.select(this).style("fill", d.data.color);
                         Tooltip.hide();

                     })
                     .merge(slice)

        slice.transition().duration(1000)
             .attrTween("d", d => {
                 this._current = this._current || d;
                 const interpolate = d3.interpolate(this._current, d);
                 this._current = interpolate(0);
                 return function(t) {
                     return arc(interpolate(t));
                 };
             })

        slice.exit()
            .remove();

        const midAngle = d => d.startAngle + (d.endAngle - d.startAngle) / 2;

        let text = svg.select(".labels").selectAll("text")
            .data(pie(data), key)

        text = text.enter()
                   .filter(d => d.data.value >= (0.05 * totalValue))  // keep labels for slices that make up >= 5%
                   .append("text")
                   .attr("dy", ".35em")
                   .text(d => d.data.abbreviation)
                   .merge(text);

        text.transition().duration(1000)
            .attrTween("transform", function(d) {
                this._current = this._current || d;
                var interpolate = d3.interpolate(this._current, d);
                this._current = interpolate(0);
                return function(t) {
                    var d2 = interpolate(t);
                    var pos = outerArc.centroid(d2);
                    pos[0] = radius * (midAngle(d2) < Math.PI ? 1 : -1);
                    return "translate(" + pos + ")";
                };
            })
            .styleTween("text-anchor", function(d) {
                this._current = this._current || d;
                var interpolate = d3.interpolate(this._current, d);
                this._current = interpolate(0);
                return function(t) {
                    var d2 = interpolate(t);
                    return midAngle(d2) < Math.PI ? "start" : "end";
                };
            });

        text.exit()
            .remove();

        let polyline = svg.select(".lines").selectAll("polyline")
            .data(pie(data), key)

        polyline.enter()
                .filter(d => d.data.value >= (0.05 * totalValue))  // keep polylines for slices that make up >= 5%
                .append("polyline")
                .transition()
                .duration(1000)
                .attrTween("points", function(d) {
                    this._current = this._current || d;
                    var interpolate = d3.interpolateObject(this._current, d);
                    this._current = interpolate(0);
                    return function(t) {
                        var d2 = interpolate(t);
                        var pos = outerArc.centroid(d2);
                        pos[0] = radius * 0.95 * (midAngle(d2) < Math.PI ? 1 : -1);
                        return [arc.centroid(d2), outerArc.centroid(d2), pos];
                    };
                });

        polyline.exit()
                .remove();

    }

    /**
     * doNonFatalError informs the user of a non-critical error.
     * @param {Error} err
     */
    doNonFatalError(err) {

        document.getElementById('non-fatal-error').innerHTML = err.message;

    }

    /**
     * clearNonFatalError clears the non-fatal error message currently being displayed.
     */
    clearNonFatalError() {

        document.getElementById('non-fatal-error').innerHTML = "";

    }

    /**
     * doFatalError locks the user interface and informs the user that there has been an unrecoverable error.
     * @param {Error} err
     */
    doFatalError(err) {

        document.getElementById('error-message').innerHTML = err.message;

        document.getElementById('loading').style.display = 'none';
        document.getElementById('cartogram').style.display = 'none';

        document.getElementById('error').style.display = 'block';

        if(this.extended_error_info !== null)
        {
            document.getElementById('error-extended-content').innerHTML = this.extended_error_info;
            document.getElementById('error-extended').style.display = 'block';
        }

    }

    /**
     * enterLoadingState locks the user interface and informs the user that a blocking operation is taking place.
     * The progress bar is hidden by default. To show it, you must call {@link Cartogram.showProgressBar} after
     * entering the loading state.
     */
    enterLoadingState() {

        /* We set the height of the loading div to the height of the previously displayed blocks */
        /* This makes transition to the loading state seem less jarring */

        var loading_height = 0;

        if(document.getElementById('cartogram').style.display !== "none")
        {
            loading_height += document.getElementById('cartogram').clientHeight;
        }

        if(document.getElementById('error').style.display !== "none")
        {
            loading_height += document.getElementById('error').clientHeight;
        }

        if(document.getElementById('piechart').style.display !== "none")
        {
            loading_height += document.getElementById('piechart').clientHeight;
        }

        // console.log(loading_height);

        /* The loading div will be at least 100px tall */
        if(loading_height > 100)
        {
            document.getElementById('loading').style.height = loading_height + "px";
        }
        else
        {
            document.getElementById('loading').style.height = "auto";
        }

        document.getElementById('loading').style.display = 'block';
        document.getElementById('cartogram').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('piechart').style.display = 'none';

        /* Disable interaction with the upload form */
        document.getElementById('upload-button').disabled = true;
        document.getElementById('edit-button').disabled = true;
        document.getElementById('handler').disabled = true;

        /* If GridEdit is open, disable updating */
        if(this.model.gridedit_window !== null && !this.model.gridedit_window.closed && typeof(this.model.gridedit_window.gridedit) === "object")
        {
            this.model.gridedit_window.gridedit.set_allow_update(false);
        }

        document.getElementById('loading-progress-container').style.display = 'none';

        this.model.in_loading_state = true;
        this.model.loading_state = null;

    }

    /**
     * showProgressBar resets the progress bar and shows it to the user when in the loading state.
     */
    showProgressBar() {

        document.getElementById('loading-progress-container').style.display = 'block';
        document.getElementById('loading-progress').style.width = "0%";

    }

    /**
     * updateProgressBar updates the value of the progress bar.
     * @param {number} min The minimum percentage value
     * @param {number} max The maximum percentage value
     * @param {number} value The current percentage value (e.g. 50)
     */
    updateProgressBar(min, max, value) {

        if(value < max)
            value = Math.max(min, value);
        else
            value = Math.min(max, value);

        document.getElementById('loading-progress').style.width = value + "%";

    }

    /**
     * exitLoadingState exits the loading state. Note that while {@link Cartogram.enterLoadingState} hides the cartogram
     * element, exitLoadingState does not unhide it. You must do this yourself.
     */
    exitLoadingState() {

        document.getElementById('loading').style.display = 'none';
        document.getElementById('upload-button').disabled = false;
        document.getElementById('edit-button').disabled = this.editButtonDisabled();
        document.getElementById('handler').disabled = false;

        /* If GridEdit is open, enable updating */
        if(this.model.gridedit_window !== null && !this.model.gridedit_window.closed && typeof(this.model.gridedit_window.gridedit) === "object")
        {
            this.model.gridedit_window.gridedit.set_allow_update(true);
        }

        this.model.in_loading_state = false;

    }

    /**
     * generateSVGDownloadLinks generates download links for the map(s) and/or cartogram(s) displayed on the left and
     * right. We do this by taking advantage of the fact that D3 generates SVG markup. We convert the SVG markup into a
     * blob URL.
     */
    generateSVGDownloadLinks() {

        var svg_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>';

        document.getElementById('map-download').onclick = (function(geojson){

            return function(e) {

                e.preventDefault();

                /*
                Append legend elements and total count to the map SVG.
                 */
                let mapArea = document.getElementById('map-area').cloneNode(true);
                let mapAreaSVG = mapArea.getElementsByTagName('svg')[0];

                // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
                mapAreaSVG.setAttribute("xmlns", "http://www.w3.org/2000/svg");

                // Increase height of SVG to accommodate legend and total.
                const mapHeight = parseFloat(mapAreaSVG.getAttribute('height'));
                mapAreaSVG.setAttribute('height', mapHeight + 100);

                let legendSVG = document.getElementById('map-area-legend').cloneNode(true);

                // Iterate legend SVG's text elements and add font attribute.
                for (let i = 0; i < legendSVG.getElementsByTagName('text').length; i++) {
                    legendSVG.getElementsByTagName('text')[i].setAttribute('font-family', 'sans-serif')
                }

                // Iterate legend SVG's elements and append them to map SVG.
                for (let i = 0; i < legendSVG.children.length; i++) {
                    let newY = parseFloat(legendSVG.children[i].getAttribute('y')) + mapHeight;
                    legendSVG.children[i].setAttribute('y', newY);
                    let newX = parseFloat(legendSVG.children[i].getAttribute('x')) + 20;
                    legendSVG.children[i].setAttribute('x', newX);
                    mapAreaSVG.appendChild(legendSVG.children[i].cloneNode(true));
                };

                // document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('map-area').innerHTML);
                document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + mapArea.innerHTML.replace(/×/g, '&#xD7;'));
                document.getElementById('download-modal-svg-link').download = "equal-area-map.svg";

                document.getElementById('download-modal-geojson-link').href = "data:application/json;base64," + window.btoa(geojson);
                document.getElementById('download-modal-geojson-link').download = "equal-area-map.geojson";

                $('#download-modal').modal();

            };

        }(JSON.stringify(this.model.map.getVersionGeoJSON("1-conventional"))));

        document.getElementById('cartogram-download').onclick = (function(geojson){

            return function(e) {

                e.preventDefault();

                /*
                Append legend elements and total count to the cartogram SVG.
                 */
                let cartogramArea = document.getElementById('cartogram-area').cloneNode(true);
                let cartogramAreaSVG = cartogramArea.getElementsByTagName('svg')[0];

                // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
                cartogramAreaSVG.setAttribute("xmlns", "http://www.w3.org/2000/svg");

                // Increase height of SVG to accommodate legend and total.
                const cartogramHeight = parseFloat(cartogramAreaSVG.getAttribute('height'));
                cartogramAreaSVG.setAttribute('height', cartogramHeight + 100);

                let legendSVG = document.getElementById('cartogram-area-legend').cloneNode(true);

                // Iterate legend SVG's text elements and add font attribute
                for (let i = 0; i < legendSVG.getElementsByTagName('text').length; i++) {
                    legendSVG.getElementsByTagName('text')[i].setAttribute('font-family', 'sans-serif')
                }

                // Iterate legend SVG's elements and append them to map SVG
                for (let i = 0; i < legendSVG.children.length; i++) {
                    let newY = parseFloat(legendSVG.children[i].getAttribute('y')) + cartogramHeight;
                    legendSVG.children[i].setAttribute('y', newY);
                    let newX = parseFloat(legendSVG.children[i].getAttribute('x')) + 20;
                    legendSVG.children[i].setAttribute('x', newX);
                    cartogramAreaSVG.appendChild(legendSVG.children[i].cloneNode(true));
                };

                //document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('cartogram-area').innerHTML);
                document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + cartogramArea.innerHTML.replace(/×/g, '&#xD7;'));
                document.getElementById('download-modal-svg-link').download = "cartogram.svg";

                document.getElementById('download-modal-geojson-link').href = "data:application/json;base64," + window.btoa(geojson);
                document.getElementById('download-modal-geojson-link').download = "cartogram.geojson";

                $('#download-modal').modal();

            };

        }(JSON.stringify(this.model.map.getVersionGeoJSON(this.model.current_sysname))));

        /*document.getElementById('map-download').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('map-area').innerHTML);
        document.getElementById('map-download').download = "map.svg";*/

        /*document.getElementById('cartogram-download').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('cartogram-area').innerHTML);
        document.getElementById('cartogram-download').download = "cartogram.svg";*/

    }

    /**
     * generateSocialMediaLinks generates social media sharing links for the given URL
     * @param {string} url The URL to generate social media sharing links for
     */
    generateSocialMediaLinks(url) {

        document.getElementById('facebook-share').href = "https://www.facebook.com/sharer/sharer.php?u=" + window.encodeURIComponent(url);

        document.getElementById('linkedin-share').href = "https://www.linkedin.com/shareArticle?url=" + window.encodeURIComponent(url) + "&mini=true&title=Cartogram&summary=Create%20cartograms%20with%20go-cart.io&source=go-cart.io";

        document.getElementById('twitter-share').href = "https://twitter.com/share?url=" + window.encodeURIComponent(url);

        document.getElementById('email-share').href = "mailto:?body=" + window.encodeURIComponent(url);

	    document.getElementById('share-link-href').value = url;

        util.addClipboard('clipboard-link', url);
    }

    /**
     * generateEmbedHTML generates the code for embedding the given cartogram
     * @param {string} mode The embedding mode ('map' for embedding the map
     *                      with no user data, and 'cart' for embedding a map
     *                      with user data
     * @param {string} key The embed key
     */
    generateEmbedHTML(mode, key) {
        var embeded_html = '<iframe src="https://go-cart.io/embed/' + mode + '/' + key + '" width="800" height="550" style="border: 1px solid black;"></iframe>'
        
        document.getElementById('share-embed-code').innerHTML = embeded_html;

        document.getElementById('share-embed').style.display = 'block';
        
        util.addClipboard('clipboard-embed', embeded_html);
    }

    /**
     * getGeneratedCartogram generates a cartogram with the given dataset, and updates the progress bar with progress
     * information from the backend.
     * @param {string} sysname The sysname of the map
     * @param {string} areas_string The areas string of the dataset
     * @param {string} unique_sharing_key The unique sharing key returned by CartogramUI
     */
    getGeneratedCartogram(sysname, areas_string, unique_sharing_key) {

        return new Promise(function(resolve, reject){

            var req_body = HTTP.serializePostVariables({
                handler: sysname,
                values: areas_string,
                unique_sharing_key: unique_sharing_key
            });

            this.setExtendedErrorInfo("");

            var progressUpdater = window.setInterval(function(cartogram_inst, key){

                return function(){

                    HTTP.get(cartogram_inst.config.getprogress_url + "?key=" + encodeURIComponent(key) + "&time=" + Date.now()).then(function(progress){

                        if(progress.progress === null)
                        {
                            cartogram_inst.updateProgressBar(5, 100, 8);
                            return;
                        }

                        let percentage = Math.floor(progress.progress * 100);

                        cartogram_inst.updateProgressBar(5, 100, percentage);

                        cartogram_inst.setExtendedErrorInfo(progress.stderr);

                    });

                };
            }(this, unique_sharing_key), 500);
            
            // HTTP.streaming(
            //     this.config.cartogram_url,
            //     "POST",
            //     {'Content-type': 'application/x-www-form-urlencoded'},
            //     req_body,
            //     {}
            // )

            HTTP.post(
                this.config.cartogram_url,
                req_body,
                {'Content-type': 'application/x-www-form-urlencoded'}
            )
                .then(function(response){

                this.clearExtendedErrorInfo();

                this.updateProgressBar(0,100,100);

                window.clearInterval(progressUpdater);

                resolve(response.cartogram_data);

            }.bind(this), function(){
                window.clearInterval(progressUpdater);
                reject(Error("There was an error retrieving the cartogram from the server."));
            });

        }.bind(this));

    }

    /**
     * displayVersionSwitchButtons displays the buttons the user can use to switch between different map versions on the
     * right.
     */
    displayVersionSwitchButtons() {

        var buttons_container = document.getElementById('map2-switch-buttons');

        // Empty the buttons container
        while(buttons_container.firstChild){
            buttons_container.removeChild(buttons_container.firstChild);
        }

        var select = document.createElement("select")
        select.className = "form-control bg-primary text-light border-primary";
        select.style.cursor = "pointer";
        select.value = this.model.current_sysname;

        // Sorting keeps the ordering of versions consistent
        Object.keys(this.model.map.versions).sort().forEach(function(sysname){

            /*var button = document.createElement('button');
            button.innerText = this.model.map.versions[sysname].name;
            if(sysname == this.model.current_sysname)
            {
                button.className = "btn btn-secondary btn-sm active";
            }
            else
            {
                button.className = "btn btn-secondary btn-sm";
                button.onclick = (function(sn){
                    return function(e){
                        this.switchVersion(sn);
                    }.bind(this);
                }.bind(this)(sysname));
            }*/

            var option = document.createElement('option');
            option.innerText = this.model.map.versions[sysname].name;
            option.value = sysname;
            option.selected = (sysname === this.model.current_sysname);

            select.appendChild(option);

        }, this);

        select.onchange = (function(cartogram_inst){

            return function(_e) {
                cartogram_inst.switchVersion(this.value);
            };

        }(this));

        buttons_container.appendChild(select);

        document.getElementById('map1-switch').style.display = 'block';
        document.getElementById('map2-switch').style.display = 'block';

    }
    
    
    /**
     * downloadTemplateFile allows download of both CSV and Excel files
     * @param {string} sysname The sysname of the new version to be displayed
     */
    async downloadTemplateFile(sysname) {
        
        document.getElementById('csv-template-link').href = this.config.cartogram_data_dir+ "/" + sysname + "/template.csv";
        document.getElementById('csv-template-link').download = sysname + "_template.csv";
        
        var csv_file_promise = HTTP.get(this.config.cartogram_data_dir+ "/" + sysname + "/template.csv", null, null, false);
        var csv_file = await csv_file_promise.then(function(response){
            return response;
        });
   
        // convert the csv file to json for easy convertion to excel file
        var lines=csv_file.split("\n");
        
        var json_file = [];
        var headers=lines[0].split(",");
        
        for(var i=1;i<lines.length - 1;i++)
        {
            var obj = {};
            var currentline=lines[i].split(",");
        
            for(var j=0;j<headers.length;j++)
            {
                obj[headers[j]] = currentline[j];
            }
        
            json_file.push(obj);
        }
        
        // convert the json_file to excel file
        const fileName = sysname + "_template.xlsx";
        const ws = XLSX.utils.json_to_sheet(json_file);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
        document.getElementById('xlsx-template-link').onclick = function() {
            XLSX.writeFile(wb, fileName);
        };
    }

    /**
    * displayCustomisePopup displays the customise popup on click on the customise button and controls the functionality of the checkboxes
    * @param {string} sysname The sysname of the new version to be displayed 
    */
   
    displayCustomisePopup(sysname) {
        
        // Toggle the display of customise popup
        
        d3.select("#map-customise").on("click", function () {
            let element = document.getElementById("map-customise-popup");
            let style = window.getComputedStyle(element);
            let display = style.getPropertyValue('display');
            if (display == "block") {
                document.getElementById("map-customise-popup").style.display = "none";
                document.getElementById("map-customise").style.backgroundColor = "#d76126";
                document.getElementById("map-customise").style.borderColor = "#d76126";
            }
            else if (display === "none") {
                document.getElementById("map-customise-popup").style.display = "block";
                document.getElementById("map-customise").style.backgroundColor = "#b75220";
                document.getElementById("map-customise").style.borderColor = "#ab4e1f";
            }
        })

        d3.select("#cartogram-customise").on("click", function () {
            let element = document.getElementById("cartogram-customise-popup");
            let style = window.getComputedStyle(element);
            let display = style.getPropertyValue('display');
            if (display == "block") {
                document.getElementById("cartogram-customise-popup").style.display = "none";
                document.getElementById("cartogram-customise").style.backgroundColor = "#d76126";
                document.getElementById("cartogram-customise").style.borderColor = "#d76126";
            }
            else if (display === "none") {
                document.getElementById("cartogram-customise-popup").style.display = "block";
                document.getElementById("cartogram-customise").style.backgroundColor = "#b75220";
                document.getElementById("cartogram-customise").style.borderColor = "#ab4e1f";
            }
        })
        
        // Toggle the gridline visibility
        
        d3.select("#gridline-toggle-map").on("change",
            function() {
                if (d3.select("#gridline-toggle-map").property("checked")) {
                    d3.select("#map-area-grid").transition()
                        .ease(d3.easeCubic)
                        .duration(500)
                        .attr("stroke-opacity", 0.4)
                    document.getElementById("map-area").dataset.gridVisibility = "on";
                }
                else {
                    d3.select("#map-area-grid").transition()
                        .ease(d3.easeCubic)
                        .duration(500)
                        .attr("stroke-opacity", 0)
                    document.getElementById("map-area").dataset.gridVisibility = "off";
                }
            })

        d3.select("#gridline-toggle-cartogram").on("change",
            function() {
                if(d3.select("#gridline-toggle-cartogram").property("checked")){
                    d3.select("#cartogram-area-grid").transition()
                        .ease(d3.easeCubic)
                        .duration(500)
                        .attr("stroke-opacity", 0.4)
                    document.getElementById("cartogram-area").dataset.gridVisibility = "on";
                }
                else {
                    d3.select("#cartogram-area-grid").transition()
                        .ease(d3.easeCubic)
                        .duration(500)
                        .attr("stroke-opacity", 0)
                    document.getElementById("cartogram-area").dataset.gridVisibility = "off";
                }
            })
            
        // Toggle legend between static and resizable
        
        d3.select("#legend-toggle-cartogram").on("change", () => {
            if (d3.select("#legend-toggle-cartogram").property("checked")) {
                this.model.map.drawResizableLegend(sysname, "cartogram-area-legend");
            }
            else {
                this.model.map.drawLegend(sysname, "cartogram-area-legend");
            }
        })
    
        d3.select("#legend-toggle-map").on("change", () => {
            if (d3.select("#legend-toggle-map").property("checked")) {
                this.model.map.drawResizableLegend('1-conventional', "map-area-legend");
            }
            else {
                this.model.map.drawLegend('1-conventional', "map-area-legend");
            }
        })
    }

    /**
     * switchVersion switches the map version displayed in the element with the given ID
     * @param {string} sysname The sysname of the new version to be displayed
     */
    switchVersion(sysname) {

        this.model.map.switchVersion(this.model.current_sysname, sysname, 'cartogram-area');

        this.model.current_sysname = sysname;

        this.displayVersionSwitchButtons();
        this.generateSVGDownloadLinks();
        this.displayCustomisePopup(sysname);
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
    async requestAndDrawCartogram(gd=null,sysname=null,update_grid_document=true) {
    
        if(this.model.in_loading_state)
            return false;

        this.clearNonFatalError();

        /* Do some validation */

        if(gd === null && document.getElementById('csv').files.length < 1)
        {
            this.doNonFatalError(Error('You must upload CSV/Excel data.'));
            return false;
        }
        
        // We check if the xlsx to csv conversion is ready; if not, we wait until it is
        this.enterLoadingState();
        this.showProgressBar();

        if(sysname === null)
        {
            sysname = document.getElementById('handler').value;
        }

        var cartogramui_promise;

        /*
        If we're submitting a grid document, convert it and pretend to upload a CSV file. Otherwise, actually upload the
        CSV file the user specified.
        */
        
        if(gd === null)
        {
            var form_data = new FormData();
            form_data.append("handler", sysname);
            
            let input_data_file = document.getElementById('csv').files[0];
            
            // if input file is xls/xlsx file
            if(input_data_file.name.split('.').pop().slice(0, 3) === 'xls') {
                await util.convertExcelToCSV(input_data_file).then(csv_file => {
                    input_data_file = csv_file;
                    form_data.append("csv", input_data_file);
                    cartogramui_promise = HTTP.post(this.config.cartogramui_url, form_data);
                });
                
            } else {
                form_data.append("csv", input_data_file);
                cartogramui_promise = HTTP.post(this.config.cartogramui_url, form_data);
            }
        }
        else
        {
            var cartogramui_req_body = this.generateCartogramUIRequestBodyFromGridDocument(sysname, gd);

            cartogramui_promise = HTTP.post(this.config.cartogramui_url, cartogramui_req_body.req_body, {
                'Content-Type': 'multipart/form-data; boundary=' + cartogramui_req_body.mime_boundary
            });
        }

        cartogramui_promise.then(function(response){

            if(response.error == "none") {

                /*
                The keys in the CartogramUI color_data are prefixed with id_. We iterate through the regions and extract
                the color information from color_data to produce a color map where the IDs are plain region IDs, as
                required by CartMap.
                */
                var colors = {};

                Object.keys(this.model.map.regions).forEach(function(region_id){

                    colors[region_id] = response.color_data["id_" + region_id];

                }, this);

                this.model.map.colors = colors;

                const pieChartButtonsContainer = document.getElementById('piechart-buttons');

                while(pieChartButtonsContainer.firstChild) {
                    pieChartButtonsContainer.removeChild(pieChartButtonsContainer.firstChild);
                }

                const noButton = document.createElement("button");
                noButton.className = "btn btn-primary";
                noButton.innerText = "Cancel";
                noButton.addEventListener('click', function(e){
                    document.getElementById('piechart').style.display = 'none';
                    document.getElementById('cartogram').style.display = 'block';
                });

                const yesButton = document.createElement("button");
                yesButton.className = "btn btn-primary mr-5";
                yesButton.innerText = "Yes, I Confirm";
                yesButton.addEventListener('click', function(sysname, response){

                    return function(e) {

                        this.enterLoadingState();
                        this.showProgressBar();

                        window.scrollTo(0, 0);

                        this.getGeneratedCartogram(sysname, response.areas_string, response.unique_sharing_key).then(function(cartogram){

                            /* We need to find out the map format. If the extrema is located in the bbox property, then we have
                                GeoJSON. Otherwise, we have the old JSON format.
                            */
                            if(cartogram.hasOwnProperty("bbox")) {

                                var extrema = {
                                    min_x: cartogram.bbox[0],
                                    min_y: cartogram.bbox[1],
                                    max_x: cartogram.bbox[2],
                                    max_y: cartogram.bbox[3]
                                };

                            // We check if the generated cartogram is a world map by checking the extent key
                            let world = false;
                            if ("extent" in cartogram) {
                                world = (cartogram.extent === 'world');
                            }

                                this.model.map.addVersion("3-cartogram", new MapVersionData(cartogram.features, extrema, response.tooltip, null, null, MapDataFormat.GEOJSON, world), "1-conventional");


                            } else {
                                this.model.map.addVersion("3-cartogram", new MapVersionData(cartogram.features, cartogram.extrema, response.tooltip,null, null,  MapDataFormat.GOCARTJSON), "1-conventional");
                            }



                            this.model.map.drawVersion("1-conventional", "map-area", ["map-area", "cartogram-area"]);
                            this.model.map.drawVersion("3-cartogram", "cartogram-area", ["map-area", "cartogram-area"]);



                            this.model.current_sysname = "3-cartogram";

                            this.generateSocialMediaLinks("https://go-cart.io/cart/" + response.unique_sharing_key);
                this.generateEmbedHTML("cart", response.unique_sharing_key);
                            this.generateSVGDownloadLinks();
                            this.displayVersionSwitchButtons();
                            this.downloadTemplateFile(sysname);
                            this.displayCustomisePopup(this.model.current_sysname);

                            if(update_grid_document) {
                                this.updateGridDocument(response.grid_document);
                            }
                            
                            // The following line draws the conventional legend when the page first loads.
                            let selectedLegendTypeMap = document.getElementById("map-area-legend").dataset.legendType;
                            let selectedLegendTypeCartogram = document.getElementById("cartogram-area-legend").dataset.legendType;
                        
                            if (selectedLegendTypeMap == "static") {
                                this.model.map.drawLegend("1-conventional", "map-area-legend", null, true);
                            }
                            else {
                                this.model.map.drawResizableLegend("1-conventional", "map-area-legend");
                            }
                            
                            if (selectedLegendTypeCartogram == "static") {
                                this.model.map.drawLegend(this.model.current_sysname, "cartogram-area-legend", null, true);
                            }
                            else {
                                this.model.map.drawResizableLegend(this.model.current_sysname, "cartogram-area-legend");
                            }
                            
                            this.model.map.drawGridLines("1-conventional", "map-area");
                            this.model.map.drawGridLines(this.model.current_sysname, "cartogram-area");

                            this.exitLoadingState();
                            document.getElementById('cartogram').style.display = "block";

                        }.bind(this), function(err){
                            this.doFatalError(err);
                            console.log(err);

                            this.drawBarChartFromTooltip('barchart', response.tooltip);
                            document.getElementById('barchart-container').style.display = "block";
                        }.bind(this))


                    }.bind(this);

                }.bind(this)(sysname, response));

                pieChartButtonsContainer.appendChild(yesButton);
                pieChartButtonsContainer.appendChild(noButton);

                this.drawPieChartFromTooltip('piechart-area', response.tooltip, colors);
                this.exitLoadingState();
                document.getElementById('piechart').style.display = 'block';

            } else {

                this.exitLoadingState();
                document.getElementById('cartogram').style.display = "block";
                this.doNonFatalError(Error(response.error));

            }

        }.bind(this), this.doFatalError); 
            
        return false;
    }

    /**
     * getPregeneratedVersion returns an HTTP get request for a pregenerated map version.
     * @param {string} sysname The sysname of the map
     * @param {string} version The sysname of the map version
     * @returns {Promise}
     */
    getPregeneratedVersion(sysname, version) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/" + version + ".json");
    }

    /**
     * getDefaultColors returns an HTTP get request for the default color scheme for a map.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getDefaultColors(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/colors.json");
    }

    /**
     * getGridDocumentTemplate returns a HTTP get request for a map's grid document template.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getGridDocumentTemplate(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/griddocument.json");
    }

    /**
     * getLabels returns an HTTP get request for the labels for the land area version of a map.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getLabels(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/labels.json");
    }

    /**
     * getAbbreviations returns an HTTP get request for the region abbreviations of a map.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getAbbreviations(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/abbreviations.json");
    }

    /**
     * getConfig returns an HTTP get request for the configuration information of a map.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getConfig(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/config.json");
    }

    /**
     * getMapMap returns an HTTP get request for all of the static data (abbreviations, original and population map
     * geometries, etc.) for a map. The progress bar is automatically updated with the download progress.
     *
     * A map pack is a JSON object containing all of this information, which used to be located in separate JSON files.
     * Combining all of this information into one file increases download speed, especially for users on mobile devices,
     * and makes it easier to display a progress bar of map information download progress, which is useful for users
     * with slow Internet connections.
     * @param {string} sysname The sysname of the map
     * @returns {Promise}
     */
    getMapPack(sysname) {
        return HTTP.get(this.config.cartogram_data_dir + "/" + sysname + "/mappack.json?v=" + this.config.version, null, function(e){

            this.updateProgressBar(0, 100, Math.floor(e.loaded / e.total * 100));

        }.bind(this));
    }

    /**
     * switchMap loads a new map with the given sysname, and displays the conventional and population versions, as well
     * as an optional extra cartogram.
     * @param {string} sysname The sysname of the new map to load
     * @param {string} hrname The human-readable name of the new map to load
     * @param {MapVersionData} cartogram An optional, extra cartogram to display
     * @param {Object.<string,string>} colors A color palette to use instead of the default one
     * @param {string} sharing_key The unique sharing key associated with this
     *                             cartogram, if any
     * @param {bool} embed Whether the method is called from embed.html or not
     */
    switchMap(sysname, hrname, cartogram=null,colors=null,sharing_key=null, embed = false) {
        if(this.model.in_loading_state)
            return;
        this.enterLoadingState();
        this.showProgressBar();

        this.getMapPack(sysname).then(function(mappack){

            var map = new CartMap(hrname, mappack.config, this.config.scale);

            /* We check if the map is a world map by searching for the 'extent' key in mappack.original.
               We then pass a boolean to the MapVersionData constructor.
             */
            let world = false;
            if ('extent' in mappack.original) {
                world = (mappack.original.extent === "world");
            }

            /* If it is a world map, we add a class name to the html elements,
               and we use this class name in implementing the CSS which draws a border
             */

            // if (world) {
            //     let conventional_map = document.getElementById("map-area");
            //     let cartogram_map = document.getElementById("cartogram-area");
            //
            //     if (!conventional_map.classList.contains('world-border')) {
            //         conventional_map.className += "world-border";
            //         cartogram_map.className += "world-border";
            //     }
            //
            // } else {
            //     let conventional_map = document.getElementById("map-area");
            //     let cartogram_map = document.getElementById("cartogram-area");
            //     conventional_map.classList.remove("world-border");
            //     cartogram_map.classList.remove("world-border");
            // }

            /* We need to find out the map format. If the extrema is located in the bbox property, then we have
               GeoJSON. Otherwise, we have the old JSON format.
            */

            if(mappack.original.hasOwnProperty("bbox")) {

                var extrema = {
                    min_x: mappack.original.bbox[0],
                    min_y: mappack.original.bbox[1],
                    max_x: mappack.original.bbox[2],
                    max_y: mappack.original.bbox[3]
                };

                map.addVersion("1-conventional", new MapVersionData(mappack.original.features, extrema, mappack.original.tooltip, mappack.abbreviations, mappack.labels, MapDataFormat.GEOJSON, world), "1-conventional");

            } else {
                map.addVersion("1-conventional", new MapVersionData(mappack.original.features, mappack.original.extrema, mappack.original.tooltip, mappack.abbreviations, mappack.labels, MapDataFormat.GOCARTJSON, world), "1-conventional");
            }

            if(mappack.population.hasOwnProperty("bbox")) {

                var extrema = {
                    min_x: mappack.population.bbox[0],
                    min_y: mappack.population.bbox[1],
                    max_x: mappack.population.bbox[2],
                    max_y: mappack.population.bbox[3]
                };

                map.addVersion("2-population", new MapVersionData(mappack.population.features, extrema, mappack.population.tooltip, null, null, MapDataFormat.GEOJSON, world), "1-conventional");

            } else {
                map.addVersion("2-population", new MapVersionData(mappack.population.features, mappack.population.extrema, mappack.population.tooltip, null, null, MapDataFormat.GOCARTJSON, world), "1-conventional");
            }

            if(cartogram !== null) {
                map.addVersion("3-cartogram", cartogram, "1-conventional");
            }

            /*
            The keys in the colors.json file are prefixed with id_. We iterate through the regions and extract the color
            information from colors.json to produce a color map where the IDs are plain region IDs, as required by
            CartMap.
            */
            var colors = {};

            Object.keys(map.regions).forEach(function(region_id){

                colors[region_id] = mappack.colors["id_" + region_id];

            }, this);

            map.colors = colors;

            map.drawVersion("1-conventional", "map-area", ["map-area", "cartogram-area"]);

            if(cartogram !== null) {
                map.drawVersion("3-cartogram", "cartogram-area", ["map-area", "cartogram-area"]);
                this.model.current_sysname = "3-cartogram";
            } else {
                map.drawVersion("2-population", "cartogram-area", ["map-area", "cartogram-area"]);
                this.model.current_sysname = "2-population";
            }

            this.model.map = map;

            this.exitLoadingState();



            if(sharing_key !== null) {
            this.generateSocialMediaLinks("https://go-cart.io/cart/" + sharing_key);
            this.generateEmbedHTML("cart", sharing_key);
            } else {
            this.generateSocialMediaLinks("https://go-cart.io/cartogram/" + sysname);
            this.generateEmbedHTML("map", sysname);
            }

            this.generateSVGDownloadLinks();
            this.displayVersionSwitchButtons();
            this.downloadTemplateFile(sysname);
            this.displayCustomisePopup(this.model.current_sysname);
            this.updateGridDocument(mappack.griddocument);
            
            let selectedLegendTypeMap = document.getElementById("map-area-legend").dataset.legendType;
            let selectedLegendTypeCartogram = document.getElementById("cartogram-area-legend").dataset.legendType;
        
            if (selectedLegendTypeMap == "static") {
                this.model.map.drawLegend("1-conventional", "map-area-legend", null, true);
            }
            else {
                this.model.map.drawResizableLegend("1-conventional", "map-area-legend");
            }
            
            if (selectedLegendTypeCartogram == "static") {
                this.model.map.drawLegend(this.model.current_sysname, "cartogram-area-legend", null, true);
            }
            else {
                this.model.map.drawResizableLegend(this.model.current_sysname, "cartogram-area-legend");
            }
            
            // The following line draws the conventional legend when the page first loads.
            this.model.map.drawGridLines("1-conventional", "map-area");
            this.model.map.drawGridLines(this.model.current_sysname, "cartogram-area");

            
            document.getElementById('cartogram').style.display = 'block';

        }.bind(this)); 
    }
}
