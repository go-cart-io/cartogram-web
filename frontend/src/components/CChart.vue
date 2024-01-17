<script setup lang="ts">
import * as d3 from 'd3'
import tinycolor from 'tinycolor2'
import { ref } from 'vue'
import type { Region } from '@/lib/region'
import type { ChartDataItem, DataTable } from '@/lib/interface'
import CTooltip from '@/components/CTooltip.vue'

import { select as d3Select } from 'd3-selection'
import { transition as d3Transition } from 'd3-transition'
d3Select.prototype.transition = d3Transition

const tooltipEl = ref<typeof CTooltip>()

const emit = defineEmits(['confirm', 'cancel'])

function drawPieChart(rawdata: DataTable) {  
  const colName = 0
  const colColor = 1
  const colValue = 2
  const container = 'piechart-area'
  const containerElement = document.getElementById(container)

  while (containerElement?.firstChild) {
    containerElement.removeChild(containerElement.firstChild)
  }

  let labelText = '', unitText = ''
  let match = rawdata.fields[colValue].label.match(/(.+)\s?\((.+)\)$/)
  if (match) {
    labelText =  match[1]
    unitText = match[2]
  }

  const width = 600,
    height = 450,
    radius = Math.min(width, height) / 2

  const svg = d3
    .select('#' + container)
    .append('svg')
    .attr('viewBox', '0 0 ' + width + ' ' + height)
    .append('g')

  svg.append('g').attr('class', 'slices')
  svg.append('g').attr('class', 'labels')
  svg.append('g').attr('class', 'lines')

  const pie = d3
    .pie<ChartDataItem>()
    .sort(null)
    .value((d) => d.value)

  const arc = d3
    .arc<d3.PieArcDatum<ChartDataItem>>()
    .outerRadius(radius * 0.8)
    .innerRadius(0)

  const outerArc = d3
    .arc<d3.PieArcDatum<ChartDataItem>>()
    .innerRadius(radius * 0.9)
    .outerRadius(radius * 0.9)

  svg.attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')')

  const dataWithOthers = Object.keys(rawdata.items)
    .map((region_id, _i, _a) => {
      return {
        label: region_id,
        value: rawdata.items[region_id][colValue],
        color: rawdata.items[region_id][colColor],
        abbreviation: rawdata.items[region_id][colName],
        name: rawdata.items[region_id][colName]
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
  document.getElementById('data-total')!.innerHTML =
    formatAsScientificNotation(total) + unitText

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

  var interpolator: any
  let slice = svg.select('.slices').selectAll<SVGPathElement, any>('path.slice').data(pie(data))

  slice = slice
    .enter()
    .insert('path')
    .style('fill', (d) => d.data.color)
    .attr('class', 'slice')
    .on('mouseover', function (event, d) {
      var color: string = tinycolor(d.data.color.toString()).brighten(20).toString()
      d3.select(this).style('fill', color)
      tooltipEl.value?.drawWithEntries(event, d.data.name, d.data.abbreviation, [
        {
          name: labelText,
          value: d.data.value,
          unit: unitText
        }
      ])
    })
    .on('mousemove', function (event, d) {
      tooltipEl.value?.drawWithEntries(event, d.data.name, d.data.abbreviation, [
        {
          name: labelText,
          value: d.data.value,
          unit: unitText
        }
      ])
    })
    .on('mouseout', function (event, d) {
      d3.select(this).style('fill', d.data.color)
      tooltipEl.value?.hide()
    })
    .merge(slice)

  slice
    .transition()
    .duration(1000)
    .attrTween('d', (d) => {
      interpolator = interpolator || d
      const interpolate = d3.interpolate(interpolator, d)
      interpolator = interpolate(0)
      return function (t) {
        return arc(interpolate(t)) as any
      }
    })

  slice.exit().remove()

  const midAngle = (d: any) => d.startAngle + (d.endAngle - d.startAngle) / 2

  let text = svg
    .select('.labels')
    .selectAll<SVGTextElement, any>('text')
    .data(pie(data), (d) => d.data.label)

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
      interpolator = interpolator || d
      var interpolate = d3.interpolate(interpolator, d)
      interpolator = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        var pos = outerArc.centroid(d2)
        pos[0] = radius * (midAngle(d2) < Math.PI ? 1 : -1)
        return 'translate(' + pos + ')'
      }
    })
    .styleTween('text-anchor', function (d) {
      interpolator = interpolator || d
      var interpolate = d3.interpolate(interpolator, d)
      interpolator = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        return midAngle(d2) < Math.PI ? 'start' : 'end'
      }
    })

  text.exit().remove()

  let polyline = svg
    .select('.lines')
    .selectAll<SVGPolylineElement, any>('polyline')
    .data(pie(data), (d) => d.data.label)

  polyline
    .enter()
    .filter((d) => d.data.value >= 0.05 * totalValue) // keep polylines for slices that make up >= 5%
    .append('polyline')
    .transition()
    .duration(1000)
    .attrTween('points', function (d) {
      interpolator = interpolator || d
      var interpolate = d3.interpolateObject(interpolator, d)
      interpolator = interpolate(0)
      return function (t) {
        var d2 = interpolate(t)
        var pos = outerArc.centroid(d2)
        pos[0] = radius * 0.95 * (midAngle(d2) < Math.PI ? 1 : -1)
        return [arc.centroid(d2), outerArc.centroid(d2), pos] as any
      }
    })

  polyline.exit().remove()
}

defineExpose({
  drawPieChart
})
</script>

<template>
  <div class="container-fluid p-3">
    <c-tooltip ref="tooltipEl" />
    <div id="piechart">
      <div class="row">
        <div>
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
      <div class="text-center" id="piechart-buttons">
        <button class="btn btn-secondary mx-2" v-on:click="emit('cancel')">Cancel</button>
        <button class="btn btn-primary" v-on:click="emit('confirm')">Yes, I Confirm</button>        
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
