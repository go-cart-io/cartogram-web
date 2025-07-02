import * as d3 from 'd3'

export function transition(fromEl: any, toEl: any, callback: () => void) {
  let transitions = 0

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
