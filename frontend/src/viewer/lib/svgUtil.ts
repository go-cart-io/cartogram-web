export function createSVGElement(
  panelID: string,
  areaLegendStr: string,
  areaUnitLegendStr: string,
  colorLegendStr: string,
  hideAreaLegend: boolean
) {
  const mapAreaSVG = document.createElementNS('http://www.w3.org/2000/svg', 'svg') as SVGSVGElement
  const MAP_SPACE = 15 // Space between color legend and map
  let extraElementHeight = 0

  // Font
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs')
  const style = document.createElementNS('http://www.w3.org/2000/svg', 'style')
  style.textContent = `@import url("https://fonts.googleapis.com/css?family=Roboto+Condensed:400,400i,700,700i");`
  defs.appendChild(style)
  mapAreaSVG.appendChild(defs)

  // Color legend
  const colorLegendSVG = document
    .getElementById('color-legend')
    ?.querySelector('svg') as SVGSVGElement
  if (colorLegendStr !== 'Region' && colorLegendSVG) {
    const colorLegendGroup = colorLegendSVG.querySelector('g')?.cloneNode(true) as SVGGElement
    if (colorLegendGroup) {
      mapAreaSVG.appendChild(colorLegendGroup)
    }

    extraElementHeight += parseFloat(colorLegendSVG.getAttribute('height') || '0') + MAP_SPACE
  }

  // Area legend title
  const areaLegendTitle = document.createElementNS(
    'http://www.w3.org/2000/svg',
    'text'
  ) as SVGGElement
  const totalStr = (document.getElementById(panelID + '-legend-total')!.textContent || '').trim()
  areaLegendTitle.textContent = `${areaLegendStr} (${totalStr} ${areaUnitLegendStr})`
  areaLegendTitle.setAttribute('font-family', 'sans-serif')
  areaLegendTitle.setAttribute('font-size', '11px')
  areaLegendTitle.setAttribute('font-weight', 'bold')
  areaLegendTitle.setAttribute('fill', '#000000')
  areaLegendTitle.setAttribute('dominant-baseline', 'text-before-edge')
  areaLegendTitle.setAttribute('x', '5')
  areaLegendTitle.setAttribute('y', extraElementHeight.toString())
  mapAreaSVG.appendChild(areaLegendTitle)
  extraElementHeight += 18

  const mainGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g') as SVGGElement
  mainGroup.setAttribute('transform', `translate(0, ${extraElementHeight})`)

  // Area legend
  if (!hideAreaLegend) addAreaLegend(panelID, mainGroup)

  // Map/Cartogram
  const visAreaSVG = document
    .getElementById(panelID + '-vis')!
    .querySelector('svg') as SVGSVGElement
  mainGroup.appendChild(visAreaSVG.querySelector('g')!.cloneNode(true) as HTMLElement)
  let visAreaWidth = visAreaSVG.getAttribute('width') || '500'
  let visAreaHeight = visAreaSVG.getAttribute('height') || '500'

  // Grid
  const gridPattern = document
    .getElementById(panelID + '-grid-area')!
    .querySelector('defs')!
    .cloneNode(true) as Element
  const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect') as SVGRectElement
  rect.setAttribute('width', visAreaWidth)
  rect.setAttribute('height', visAreaHeight)
  rect.setAttribute('fill', 'url(#c-area2-grid)')
  mainGroup.appendChild(gridPattern)
  mainGroup.appendChild(rect)

  // Finalize svg attributes
  const finalHeight = (parseFloat(visAreaHeight) + extraElementHeight).toString()
  mapAreaSVG.setAttribute('fill', 'none')
  mapAreaSVG.appendChild(mainGroup)
  mapAreaSVG.setAttribute('width', visAreaWidth)
  mapAreaSVG.setAttribute('height', finalHeight)
  mapAreaSVG.setAttribute('viewBox', `0 0 ${visAreaWidth} ${finalHeight}`)
  mapAreaSVG.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  return mapAreaSVG
}

function addAreaLegend(panelID: string, mainGroup: SVGGElement) {
  const legendSVG = document.getElementById(panelID + '-legend')
  if (legendSVG) {
    // Square
    const areaLegendGroup = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'g'
    ) as SVGGElement
    areaLegendGroup.appendChild(legendSVG.querySelector('g')!.cloneNode(true) as HTMLElement)
    areaLegendGroup.setAttribute('width', legendSVG.getAttribute('width') || '0')
    areaLegendGroup.setAttribute('height', legendSVG.getAttribute('height') || '0')
    mainGroup.appendChild(areaLegendGroup)

    const areaLegendText = document.createElement('text')
    const legendTextX = 6 + parseFloat(legendSVG.getAttribute('width')!)
    const legendTextY = parseFloat(legendSVG.getAttribute('height') || '0') / 2
    areaLegendText.textContent = document.getElementById(panelID + '-legend-num')!.textContent || ''
    areaLegendText.setAttribute('font-family', 'sans-serif')
    areaLegendText.setAttribute('font-size', '11px')
    areaLegendText.setAttribute('x', legendTextX.toString())
    areaLegendText.setAttribute('y', legendTextY.toString())
    areaLegendText.setAttribute('fill', '#000000')
    areaLegendText.setAttribute('dominant-baseline', 'middle')
    mainGroup.appendChild(areaLegendText)

    return mainGroup
  }
}
