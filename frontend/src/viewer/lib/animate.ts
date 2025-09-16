import * as d3 from 'd3'

export function geoTransition(id: string, callback: () => void) {
  // Use an object to maintain reference across function calls
  const transitionCounter: TransitionCounter = { count: 0 }

  const fromEl = d3.select('#' + id + '-vis')
  const toEl = d3.select('#' + id + '-offscreen')

  fromEl.selectAll('path[aria-roledescription="geoshape"]').each(function (this: any) {
    const geoID = d3.select(this).attr('aria-label')

    // Animate polygons
    const toPathEl = toEl.select('path[aria-label="' + geoID + '"]')
    if (!toPathEl.empty()) {
      createTransition(d3.select(this), transitionCounter, callback).attr('d', toPathEl.attr('d'))
    }

    // Animate background polygons (to support non-contiguous, etc.)
    const bgGeoID = geoID.replace('geoshape', 'geobg')
    const toBGPathEl = toEl.select('path[aria-label="' + bgGeoID + '"]')
    if (!toBGPathEl.empty()) {
      createTransition(
        fromEl.select('path[aria-label="' + bgGeoID + '"]'),
        transitionCounter,
        callback
      ).attr('d', toBGPathEl.attr('d'))
    }

    // Animate labels
    const labelID = geoID.replace('geoshape', 'geolabel')
    if (!labelID || labelID === 'dividers') return
    const toLabelEl = toEl.select('text[aria-label="' + labelID + '"]')
    if (!toLabelEl.empty()) {
      createTransition(
        fromEl.select('text[aria-label="' + labelID + '"]'),
        transitionCounter,
        callback
      )
        .attr('transform', toLabelEl.attr('transform'))
        .attr('opacity', toLabelEl.attr('opacity'))
        .attr('font-size', toLabelEl.attr('font-size'))
    }
  })

  // Animate dividers
  fromEl.selectAll('path[aria-roledescription="geodivider"]').each(function (this: any) {
    const geoID = d3.select(this).attr('aria-label')

    // Animate polygons
    const toPathEl = toEl.select('path[aria-label="' + geoID + '"]')
    if (!toPathEl.empty()) {
      createTransition(d3.select(this), transitionCounter, callback).attr('d', toPathEl.attr('d'))
    }
  })
}

// Type for the transition counter object
type TransitionCounter = {
  count: number
}

// Helper function to create transitions with shared counter
function createTransition(
  selection: d3.Selection<any, any, any, any>,
  counter: TransitionCounter,
  callback: () => void
) {
  return selection
    .transition()
    .ease(d3.easeCubic)
    .duration(1000)
    .on('start', function () {
      counter.count++
    })
    .on('end', function () {
      if (--counter.count === 0) callback()
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
