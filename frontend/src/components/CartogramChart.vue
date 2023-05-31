<script setup lang="ts">
import * as d3 from 'd3'
import tinycolor from 'tinycolor2'
import { ref } from 'vue'
import type { Region } from '@/lib/region'
import Tooltip from '@/components/Tooltip.vue'

const tooltipEl = ref<typeof Tooltip>()

const emit = defineEmits(['confirm', 'cancel'])

function drawPieChartFromTooltip(
  regions: { [key: string]: Region },
  tooltip: any,
  colors: { [key: string]: string } = {}
) {
  console.log(colors)
  const container = 'piechart-area'
  const containerElement = document.getElementById(container)

  while (containerElement.firstChild) {
    containerElement.removeChild(containerElement.firstChild)
  }

  const svg = d3
    .select('#' + container)
    .append('svg')
    .append('g')

  svg.append('g').attr('class', 'slices')
  svg.append('g').attr('class', 'labels')
  svg.append('g').attr('class', 'lines')

  const width = 600,
    height = 450,
    radius = Math.min(width, height) / 2

  const pie = d3
    .pie()
    .sort(null)
    .value((d) => d.value)

  const arc = d3
    .arc()
    .outerRadius(radius * 0.8)
    .innerRadius(0)

  const outerArc = d3
    .arc()
    .innerRadius(radius * 0.9)
    .outerRadius(radius * 0.9)

  svg.attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')')

  const key = (d) => d.data.label

  const dataWithOthers = Object.keys(regions)
    .map((region_id, _i, _a) => {
      return {
        label: region_id,
        value: tooltip.data['id_' + region_id].value,
        color: colors['id_' + region_id],
        abbreviation: regions[region_id].abbreviation,
        name: regions[region_id].name
      }
    })
    .filter((d) => d.value !== 'NA')

  const formatAsScientificNotation = (num: number) => {
    const rounded = num.toPrecision(4)
    const parts = rounded.split('e')

    if (parts.length === 2) {
      return `${parts[0]}&nbsp;&times;&nbsp;10<sup>${parts[1].replace('+', '')}</sup>`
    } else {
      return rounded
    }
  }

  const total = dataWithOthers.reduce((acc, datum) => acc + datum.value, 0)
  document.getElementById('data-total').innerHTML =
    formatAsScientificNotation(total) + (tooltip.unit === '' ? '' : ' ' + tooltip.unit)

  const othersThreshold = total * 0.025

  let others = {
    label: '_others',
    value: 0,
    color: '#aaaaaa',
    abbreviation: 'Others',
    name: 'Others'
  }

  dataWithOthers.forEach((datum) => {
    if (datum.value < othersThreshold) {
      others.value += datum.value
    }
  })

  let data = dataWithOthers

  if (others.value > 0) {
    data = dataWithOthers.filter((d) => d.value >= othersThreshold)
    data.push(others)
  }

  // Reorder the data to reduce neighboring regions having the same color

  for (let i = 0; i < data.length; i++) {
    // If the (i + 1)th has the same color as ith slice...
    if (data[i].color === data[(i + 1) % data.length].color) {
      // Try to find a slice *different* color, such that swapping it won't result in neighboring slices
      // having the same color.
      // If we find one, swap it with the (i + 1)th slice.
      for (let j = i + 2; j < data.length + i + 2; j++) {
        if (
          data[j % data.length].color !== data[(i + 1) % data.length].color &&
          data[(j + 1) % data.length].color !== data[(i + 1) % data.length].color &&
          data[(j - 1) % data.length].color !== data[(i + 1) % data.length].color
        ) {
          const temp = data[j % data.length]
          data[j % data.length] = data[(i + 1) % data.length]
          data[(i + 1) % data.length] = temp
          break
        }
      }
    }
  }

  const totalValue = data.reduce(
    (total, d, _i, _a) => (d.value !== 'NA' ? total + d.value : total),
    0
  )

  let slice = svg.select('.slices').selectAll('path.slice').data(pie(data))

  slice = slice
    .enter()
    .insert('path')
    .style('fill', (d) => d.data.color)
    .attr('class', 'slice')
    .on('mouseover', function (event, d) {
      d3.select(this).style('fill', tinycolor(d.data.color).brighten(20))

      tooltipEl.value.drawWithEntries(event, d.data.name, d.data.abbreviation, [
        {
          name: tooltip.label,
          value: d.data.value,
          unit: tooltip.unit
        }
      ])
    })
    .on('mousemove', function (event, d) {
      tooltipEl.value.drawWithEntries(event, d.data.name, d.data.abbreviation, [
        {
          name: tooltip.label,
          value: d.data.value,
          unit: tooltip.unit
        }
      ])
    })
    .on('mouseout', function (event, d) {
      d3.select(this).style('fill', d.data.color)
      tooltipEl.value.hide()
    })
    .merge(slice)

  slice
    .transition()
    .duration(1000)
    .attrTween('d', (d) => {
      this._current = this._current || d
      const interpolate = d3.interpolate(this._current, d)
      this._current = interpolate(0)
      return function (t) {
        return arc(interpolate(t))
      }
    })

  slice.exit().remove()

  const midAngle = (d) => d.startAngle + (d.endAngle - d.startAngle) / 2

  let text = svg.select('.labels').selectAll('text').data(pie(data), key)

  text = text
    .enter()
    .filter((d) => d.data.value >= 0.05 * totalValue) // keep labels for slices that make up >= 5%
    .append('text')
    .attr('dy', '.35em')
    .text((d) => d.data.abbreviation)
    .merge(text)

  text
    .transition()
    .duration(1000)
    .attrTween('transform', function (d) {
      this._current = this._current || d
      var interpolate = d3.interpolate(this._current, d)
      this._current = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        var pos = outerArc.centroid(d2)
        pos[0] = radius * (midAngle(d2) < Math.PI ? 1 : -1)
        return 'translate(' + pos + ')'
      }
    })
    .styleTween('text-anchor', function (d) {
      this._current = this._current || d
      var interpolate = d3.interpolate(this._current, d)
      this._current = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        return midAngle(d2) < Math.PI ? 'start' : 'end'
      }
    })

  text.exit().remove()

  let polyline = svg.select('.lines').selectAll('polyline').data(pie(data), key)

  polyline
    .enter()
    .filter((d) => d.data.value >= 0.05 * totalValue) // keep polylines for slices that make up >= 5%
    .append('polyline')
    .transition()
    .duration(1000)
    .attrTween('points', function (d) {
      this._current = this._current || d
      var interpolate = d3.interpolateObject(this._current, d)
      this._current = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        var pos = outerArc.centroid(d2)
        pos[0] = radius * 0.95 * (midAngle(d2) < Math.PI ? 1 : -1)
        return [arc.centroid(d2), outerArc.centroid(d2), pos]
      }
    })

  polyline.exit().remove()
}

// /**
//  * drawChartFromTooltip draws a barchart of the uploaded dataset, which can be found in the tooltip of the
//  * CartogramUI response. We use this when CartogramUI returns a success response, but cartogram generation fails.
//  * @param {string} container The ID of the element to draw the barchart in
//  * @param {Object} tooltip The tooltip to retrieve the data from
//  */
//  drawBarChartFromTooltip(container, tooltip) {
//   var margin = { top: 5, right: 5, bottom: 5, left: 50 },
//     width = 800 - margin.left - margin.right,
//     height = 400 - margin.top - margin.bottom

//   // ranges
//   var x = d3.scaleBand().rangeRound([0, width]).padding(0.05)

//   var y = d3.scaleLinear().range([height, 0])

//   // axes
//   var xAxis = d3.axisBottom(x)

//   var yAxis = d3.axisLeft(y).ticks(10)

//   // SVG element
//   var svg = d3
//     .select('#' + container)
//     .append('svg')
//     .attr('width', width + margin.left + margin.right)
//     .attr('height', height + margin.top + margin.bottom)
//     .append('g')
//     .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

//   // Data formatting
//   var data = new Array()

//   Object.keys(tooltip.data).forEach(function (key, index) {
//     data.push(tooltip.data[key])
//   })

//   /* Display in alphabetical order */
//   data.sort(function (a, b) {
//     if (a.name < b.name) return -1
//     else if (a.name > b.name) return 1
//     else return 0
//   })

//   // scale the range of the data
//   x.domain(
//     data.map(function (d) {
//       return d.name
//     })
//   )
//   y.domain([
//     0,
//     d3.max(data, function (d) {
//       return d.value
//     }) + 5
//   ])

//   // add axes
//   svg
//     .append('g')
//     .attr('class', 'x axis')
//     .attr('transform', 'translate(0,' + height + ')')
//     .call(xAxis)
//     .selectAll('text')
//     .style('text-anchor', 'end')
//     .attr('dx', '-.8em')
//     .attr('dy', '-.55em')
//     .attr('transform', 'rotate(-90)')

//   svg
//     .append('g')
//     .attr('class', 'y axis')
//     .call(yAxis)
//     .append('text')
//     .attr('transform', 'rotate(-90)')
//     .attr('y', 5)
//     .attr('dy', '.71em')
//     .style('text-anchor', 'end')
//     .text('User Data')

//   // add the bar chart
//   svg
//     .selectAll('bar')
//     .data(data)
//     .enter()
//     .append('rect')
//     .attr('class', 'bar')
//     .attr('x', function (d) {
//       return x(d.name)
//     })
//     .attr('width', x.bandwidth())
//     .attr('y', function (d) {
//       return y(d.value)
//     })
//     .attr('height', function (d) {
//       return height - y(d.value)
//     })
// }

defineExpose({
  drawPieChartFromTooltip
})
</script>

<template>
  <div>
    <Tooltip ref="tooltipEl" />
    <div id="barchart-container" style="display: none">
      <p>
        Your cartogram was unable to be generated due to an error. You may make use of this barchart
        instead, or refresh the page and try again.
      </p>

      <div id="barchart" style="height: 600px"></div>
    </div>

    <div id="piechart">
      <div class="row">
        <div class="col-md-6">
          <h4>Confirm your data are appropriate for a cartogram</h4>
          <p>
            Your data sums to an approximate total of <b id="data-total"></b>. Is this a
            <a href="/faq#what-kind-of-data">meaningful quantity</a>? Additionally, you may consider
            the pie chart below. If it is an acceptable visualization for your dataset, then you can
            present your data as a cartogram. Otherwise, please choose a different dataset to
            continue.
          </p>
        </div>
      </div>
      <div id="piechart-area"></div>
      <div class="row" id="piechart-buttons">
        <button class="btn btn-primary mr-5" v-on:click="emit('confirm')">Yes, I Confirm</button>
        <button class="btn btn-primary" v-on:click="emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style>
#barchart svg {
  overflow: visible !important;
}

#barchart text.label {
  font-size: 0.8rem;
  letter-spacing: -0.01rem;
}

#piechart-area svg {
  width: 960px;
  height: 450px;
}

path.slice {
  stroke-width: 2px;
}

polyline {
  opacity: 0.3;
  stroke: black;
  stroke-width: 2px;
  fill: none;
}

.bar {
  fill: steelblue;
}

.bar:hover {
  fill: brown;
}

.axis {
  font: 11px sans-serif;
}

.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}
</style>
