import * as d3 from 'd3'

export function geoTransition(id: string, callback: () => void) {
  let transitions = 0
  const fromEl = d3.select('#' + id + '-vis')
  const toEl = d3.select('#' + id + '-offscreen')

  fromEl.selectAll('path[aria-roledescription="geoshape"]').each(function (this: any) {
    const geoID = d3.select(this).attr('aria-label')
    const labelID = geoID.replace('geoshape', 'geolabel')

    const newD = toEl.select('path[aria-label="' + geoID + '"]').attr('d')
    d3.select(this)
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('d', newD)
      .on('start', function () {
        transitions++
      })
      .on('end', function () {
        if (--transitions === 0) callback()
      })

    if (!labelID || labelID === 'dividers') return
    const labelEl = toEl.select('text[aria-label="' + labelID + '"]')
    const newLabelPos = labelEl.attr('transform')
    const newLabelOpacity = labelEl.attr('opacity')
    const newLabelSize = labelEl.attr('font-size')
    fromEl
      .select('text[aria-label="' + labelID + '"]')
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('transform', newLabelPos)
      .attr('opacity', newLabelOpacity)
      .attr('font-size', newLabelSize)
      .on('start', function () {
        transitions++
      })
      .on('end', function () {
        if (--transitions === 0) callback()
      })
  })
}

export function gridTransition(id: string, gridWidth: number) {
  const gridPattern = d3.select('#' + id)
  if (isNaN(gridWidth) || !gridPattern) return

  // *5 for pretty transition when resize grid
  gridPattern.select('path').attr('d', 'M ' + gridWidth * 5 + ' 0 L 0 0 0 ' + gridWidth * 5)

  if (gridPattern.attr('width')) {
    // To prevent transition from 0
    gridPattern
      .transition()
      .ease(d3.easeCubic)
      .duration(1000)
      .attr('width', gridWidth)
      .attr('height', gridWidth)
  } else {
    gridPattern.attr('width', gridWidth).attr('height', gridWidth)
  }
}
