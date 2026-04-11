<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Modal } from 'bootstrap'
import * as d3 from 'd3'
import type { FeatureCollection, Feature } from 'geojson'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()

const props = defineProps<{
  columns: Array<{
    index: number
    label: string
  }>
}>()

const emit = defineEmits<{
  proceed: [switchColumns: string[]]
}>()

let modalInstance: Modal | null = null
const modalEl = ref<HTMLElement | null>(null)
const mapContainer = ref<HTMLElement | null>(null)
const currentStep = ref(0)

// Track which columns the user confirmed as non-additive (should switch to choropleth)
const columnsToSwitch = ref<string[]>([])

const currentCol = computed(() => props.columns[currentStep.value] ?? null)

const regionPair = computed(() => {
  if (!currentCol.value) return null
  const items = store.dataTable.items
  const label = currentCol.value.label
  const geojson = store.geojsonData
  const regionCol = store.geojsonRegionCol
  if (items.length < 2 || !geojson) return null

  const featuresByRegion = new Map<string, Feature>()
  for (const f of geojson.features) {
    if (f.properties) {
      featuresByRegion.set(f.properties[regionCol], f)
    }
  }

  const areaLabel = store.dataTable.fields.find(
    (f: any) => f.name === 'Geographic Area' || f.label === 'Geographic Area'
  )?.label ?? 'Geographic Area'

  const candidates = items
    .filter((item: any) => {
      const val = parseFloat(item[label] as string)
      const area = parseFloat(item[areaLabel])
      return !isNaN(val) && val > 0 && !isNaN(area) && area > 0
        && item.Region && featuresByRegion.has(item.Region as string)
    })
    .map((item: any) => ({
      region: item.Region as string,
      value: parseFloat(item[label]),
      feature: featuresByRegion.get(item.Region as string)!,
      area: parseFloat(item[areaLabel])
    }))

  let bestPair: typeof candidates[0] extends infer T ? { a: T; b: T; score: number } | null : never = null

  for (let i = 0; i < candidates.length; i++) {
    for (let j = i + 1; j < candidates.length; j++) {
      const a = candidates[i], b = candidates[j]
      const relDiff = Math.abs(a.value - b.value) / Math.min(a.value, b.value)
      const sizeScore = Math.min(a.area, b.area)
      const score = sizeScore * relDiff
      if (!bestPair || score > bestPair.score) {
        bestPair = { a, b, score }
      }
    }
  }

  if (bestPair) {
    return {
      regionA: bestPair.a.region, regionB: bestPair.b.region,
      valueA: bestPair.a.value, valueB: bestPair.b.value,
      featureA: bestPair.a.feature, featureB: bestPair.b.feature
    }
  }
  return null
})

const sumValue = computed(() => {
  if (!regionPair.value) return 0
  return regionPair.value.valueA + regionPair.value.valueB
})

const avgValue = computed(() => {
  if (!regionPair.value) return 0
  return (regionPair.value.valueA + regionPair.value.valueB) / 2
})

const mapTotal = computed(() => {
  if (!currentCol.value) return { sum: 0, avg: 0, count: 0 }
  const label = currentCol.value.label
  let sum = 0
  let count = 0
  for (const item of store.dataTable.items) {
    const val = parseFloat(item[label] as string)
    if (!isNaN(val)) {
      sum += val
      count++
    }
  }
  return { sum, avg: count > 0 ? sum / count : 0, count }
})

const questionPhase = ref<'merge' | 'total'>('merge')

function formatNum(n: number): string {
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''
  if (abs >= 1_000_000_000) return sign + (abs / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B'
  if (abs >= 1_000_000) return sign + (abs / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (abs >= 10_000) return sign + (abs / 1_000).toFixed(1).replace(/\.0$/, '') + 'K'
  if (Number.isInteger(n)) return n.toLocaleString()
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

const currentUnit = computed(() => {
  if (!currentCol.value) return ''
  const field = store.dataTable.fields[currentCol.value.index]
  return field?.unit ? ` ${field.unit}` : ''
})

function drawMiniMap() {
  if (!mapContainer.value || !store.geojsonData || !regionPair.value) return

  const container = mapContainer.value
  container.innerHTML = ''

  const width = container.clientWidth || 320
  const height = 180
  const pair = regionPair.value

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const focusCollection: FeatureCollection = {
    type: 'FeatureCollection',
    features: [pair.featureA, pair.featureB]
  }

  const padding = 20
  const projection = d3.geoIdentity().reflectY(true).fitExtent(
    [[padding, padding], [width - padding, height - padding]],
    focusCollection
  )

  const path = d3.geoPath().projection(projection)

  svg
    .selectAll('path.bg')
    .data(store.geojsonData.features)
    .enter()
    .append('path')
    .attr('class', 'bg')
    .attr('d', path as any)
    .attr('fill', '#e9ecef')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 0.5)

  svg.append('path').datum(pair.featureA).attr('d', path as any)
    .attr('fill', '#268bd2').attr('stroke', '#1a6aa5').attr('stroke-width', 1.5).attr('opacity', 0.85)

  svg.append('path').datum(pair.featureB).attr('d', path as any)
    .attr('fill', '#d76127').attr('stroke', '#a84b1e').attr('stroke-width', 1.5).attr('opacity', 0.85)

  function addLabel(cx: number, cy: number, text: string, bgColor: string) {
    if (!cx || !cy) return
    const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)
    const textEl = g.append('text')
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
      .attr('font-size', '13px').attr('font-weight', 'bold')
      .attr('font-family', 'system-ui, sans-serif').attr('fill', '#fff')
      .text(text)
    const bbox = (textEl.node() as SVGTextElement).getBBox()
    g.insert('rect', 'text')
      .attr('x', bbox.x - 4).attr('y', bbox.y - 2)
      .attr('width', bbox.width + 8).attr('height', bbox.height + 4)
      .attr('rx', 3).attr('fill', bgColor).attr('opacity', 0.9)
  }

  const centroidA = path.centroid(pair.featureA as any)
  const centroidB = path.centroid(pair.featureB as any)
  addLabel(centroidA[0], centroidA[1], formatNum(pair.valueA), '#268bd2')
  addLabel(centroidB[0], centroidB[1], formatNum(pair.valueB), '#d76127')
}

function drawMiniMapAll() {
  if (!mapContainer.value || !store.geojsonData) return

  const container = mapContainer.value
  container.innerHTML = ''

  const width = container.clientWidth || 320
  const height = 180

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const projection = d3.geoIdentity().reflectY(true).fitSize([width - 16, height - 16], store.geojsonData)
  const path = d3.geoPath().projection(projection)

  svg
    .selectAll('path')
    .data(store.geojsonData.features)
    .enter()
    .append('path')
    .attr('d', path as any)
    .attr('fill', '#268bd2')
    .attr('stroke', '#1a6aa5')
    .attr('stroke-width', 0.5)
    .attr('opacity', 0.7)
}

watch(currentStep, () => {
  questionPhase.value = 'merge'
  nextTick(() => drawMiniMap())
})

function open() {
  currentStep.value = 0
  questionPhase.value = 'merge'
  columnsToSwitch.value = []
  if (modalEl.value) {
    modalInstance = new Modal(modalEl.value, { backdrop: 'static', keyboard: false })
    modalInstance.show()
    nextTick(() => drawMiniMap())
  }
}

function finish() {
  modalInstance?.hide()
  emit('proceed', columnsToSwitch.value)
}

const mergeVote = ref<'sum' | 'average' | 'skip'>('skip')

function advanceToNextColumn() {
  if (currentStep.value < props.columns.length - 1) {
    currentStep.value++
  } else {
    finish()
  }
}

function answer(userAnswer: 'sum' | 'average' | 'skip') {
  if (!currentCol.value) return

  if (questionPhase.value === 'merge') {
    mergeVote.value = userAnswer
    questionPhase.value = 'total'
    nextTick(() => drawMiniMapAll())
    return
  }

  // Phase 'total' — combine both votes
  const totalVote = userAnswer
  const finalVote =
    totalVote !== 'skip' ? totalVote : mergeVote.value !== 'skip' ? mergeVote.value : 'skip'

  // If user confirmed it's not additive (average), mark for choropleth switch
  if (finalVote === 'average') {
    columnsToSwitch.value.push(currentCol.value.label)
  }

  advanceToNextColumn()
}

function switchAll() {
  // Mark all remaining columns for choropleth switch
  for (let i = currentStep.value; i < props.columns.length; i++) {
    if (!columnsToSwitch.value.includes(props.columns[i].label)) {
      columnsToSwitch.value.push(props.columns[i].label)
    }
  }
  finish()
}

defineExpose({ open })
</script>

<template>
  <div ref="modalEl" class="modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered">
      <div class="modal-content" v-if="currentCol">
        <div class="modal-header bg-warning-subtle border-warning">
          <h5 class="modal-title">
            <i class="fa-solid fa-triangle-exclamation text-warning me-2"></i>
            <strong>{{ currentCol.label }}</strong> may not be suitable for a cartogram
          </h5>
        </div>
        <div class="modal-body">
          <p class="mb-1">
            In a cartogram, each region's area represents its data value.
            When two regions are combined, their areas add up — so the data
            must also add up for the map to remain meaningful. This property
            is called <strong>extensivity</strong>.
          </p>
          <p class="mb-2">
            Our statistical model suggests <strong>{{ currentCol.label }}</strong>
            may violate extensivity. Please verify:
          </p>

          <div v-if="regionPair">
            <div
              ref="mapContainer"
              class="sense-check-map border rounded mb-3"
            ></div>

            <!-- PHASE 1: Merge question -->
            <template v-if="questionPhase === 'merge'">
              <div class="d-flex gap-3 mb-3">
                <span>
                  <span class="sense-dot sense-dot-a"></span>
                  {{ regionPair.regionA }}:
                  <strong>{{ formatNum(regionPair.valueA) }}{{ currentUnit }}</strong>
                </span>
                <span>
                  <span class="sense-dot sense-dot-b"></span>
                  {{ regionPair.regionB }}:
                  <strong>{{ formatNum(regionPair.valueB) }}{{ currentUnit }}</strong>
                </span>
              </div>

              <p class="mb-2">
                <strong>If these two regions merged, would the combined
                <em>{{ currentCol.label }}</em> be closer to…</strong>
              </p>

              <div class="d-flex flex-column gap-2">
                <button class="btn btn-outline-primary text-start sense-btn" @click="answer('sum')">
                  <span class="sense-btn-value">~{{ formatNum(sumValue) }}{{ currentUnit }}</span>
                  <span class="sense-btn-hint">
                    The sum — like total population, regionwide GDP, number of hospitals
                  </span>
                </button>
                <button class="btn btn-outline-primary text-start sense-btn" @click="answer('average')">
                  <span class="sense-btn-value">~{{ formatNum(avgValue) }}{{ currentUnit }}</span>
                  <span class="sense-btn-hint">
                    Somewhere between the two — like temperature, population density (people per km²), average life expectancy
                  </span>
                </button>
                <button class="btn btn-link text-muted text-start small" @click="answer('skip')">
                  Not sure — skip
                </button>
              </div>
            </template>

            <!-- PHASE 2: Total for the entire map -->
            <template v-else-if="questionPhase === 'total'">
              <p class="mb-2">
                <strong>Now consider all {{ mapTotal.count }} regions together.
                Is <em>{{ currentCol.label }}</em> for the whole map closer to…</strong>
              </p>

              <div class="d-flex flex-column gap-2">
                <button class="btn btn-outline-primary text-start sense-btn" @click="answer('sum')">
                  <span class="sense-btn-value">
                    ~{{ formatNum(mapTotal.sum) }}{{ currentUnit }} (the sum)
                  </span>
                  <span class="sense-btn-hint">
                    Adding up makes sense — e.g. total population, total exports, number of hospitals
                  </span>
                </button>
                <button class="btn btn-outline-primary text-start sense-btn" @click="answer('average')">
                  <span class="sense-btn-value">
                    ~{{ formatNum(mapTotal.avg) }}{{ currentUnit }} (the average)
                  </span>
                  <span class="sense-btn-hint">
                    Summing doesn't make sense — e.g. temperature, average life expectancy, percentages
                  </span>
                </button>
                <button class="btn btn-link text-muted text-start small" @click="answer('skip')">
                  Not sure — create cartogram anyway
                </button>
              </div>
            </template>
          </div>

          <div v-else class="text-muted">
            Not enough data to generate a question for this column.
            <button class="btn btn-link" @click="answer('skip')">Skip</button>
          </div>
        </div>
        <div class="modal-footer justify-content-end">
          <button class="btn btn-outline-warning btn-sm" @click="switchAll()">
            Try a choropleth instead
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sense-check-map {
  width: 100%;
  height: 180px;
  background: #f8f9fa;
  overflow: hidden;
}

.sense-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  vertical-align: middle;
  margin-right: 4px;
}

.sense-dot-a {
  background: #268bd2;
}

.sense-dot-b {
  background: #d76127;
}

.sense-btn {
  padding: 0.6rem 1rem;
}

.sense-btn-value {
  display: block;
  font-size: 1.1em;
  font-weight: 600;
}

.sense-btn-hint {
  display: block;
  font-size: 0.85em;
  color: #6c757d;
  margin-top: 2px;
}
</style>
