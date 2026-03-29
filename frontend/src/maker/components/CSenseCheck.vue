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
    recommendation: { type: string; reason: string; confidence?: number | null }
  }>
}>()

const emit = defineEmits(['done'])

let modalInstance: Modal | null = null
const modalEl = ref<HTMLElement | null>(null)
const mapContainer = ref<HTMLElement | null>(null)
const currentStep = ref(0)

const currentCol = computed(() => props.columns[currentStep.value] ?? null)

// Pick two neighbouring regions with distinct values for the current column
const regionPair = computed(() => {
  if (!currentCol.value) return null
  const items = store.dataTable.items
  const label = currentCol.value.label
  const geojson = store.geojsonData
  const regionCol = store.geojsonRegionCol
  if (items.length < 2 || !geojson) return null

  // Build adjacency from bounding box overlap (approximate neighbours)
  const featuresByRegion = new Map<string, Feature>()
  for (const f of geojson.features) {
    if (f.properties) {
      featuresByRegion.set(f.properties[regionCol], f)
    }
  }

  // Try to find two regions with different values, prefer adjacent ones
  // but fall back to any two distinct-valued regions
  let bestPair: {
    regionA: string
    regionB: string
    valueA: number
    valueB: number
    featureA: Feature
    featureB: Feature
  } | null = null

  for (let i = 0; i < items.length && i < 20; i++) {
    for (let j = i + 1; j < items.length && j < 20; j++) {
      const valA = parseFloat(items[i][label])
      const valB = parseFloat(items[j][label])
      if (isNaN(valA) || isNaN(valB) || valA === valB) continue
      if (!items[i].Region || !items[j].Region) continue

      const fA = featuresByRegion.get(items[i].Region as string)
      const fB = featuresByRegion.get(items[j].Region as string)
      if (!fA || !fB) continue

      if (!bestPair) {
        bestPair = {
          regionA: items[i].Region as string,
          regionB: items[j].Region as string,
          valueA: valA,
          valueB: valB,
          featureA: fA,
          featureB: fB
        }
      }
      // Prefer both positive and reasonably different
      if (valA > 0 && valB > 0 && Math.abs(valA - valB) > Math.min(valA, valB) * 0.1) {
        return {
          regionA: items[i].Region as string,
          regionB: items[j].Region as string,
          valueA: valA,
          valueB: valB,
          featureA: fA,
          featureB: fB
        }
      }
    }
  }
  return bestPair
})

const sumValue = computed(() => {
  if (!regionPair.value) return 0
  return regionPair.value.valueA + regionPair.value.valueB
})

const avgValue = computed(() => {
  if (!regionPair.value) return 0
  return (regionPair.value.valueA + regionPair.value.valueB) / 2
})

// Compute the total and average across ALL regions for the "whole map" question
const mapTotal = computed(() => {
  if (!currentCol.value) return { sum: 0, avg: 0, count: 0 }
  const label = currentCol.value.label
  let sum = 0
  let count = 0
  for (const item of store.dataTable.items) {
    const val = parseFloat(item[label])
    if (!isNaN(val)) {
      sum += val
      count++
    }
  }
  return { sum, avg: count > 0 ? sum / count : 0, count }
})

// Two-phase questioning: 'merge' then 'total'
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

const algoSuggestion = computed(() => {
  if (!currentCol.value) return ''
  return currentCol.value.recommendation.type
})

// Draw the mini map highlighting the two selected regions
function drawMiniMap() {
  if (!mapContainer.value || !store.geojsonData || !regionPair.value) return

  const container = mapContainer.value
  container.innerHTML = ''

  const width = container.clientWidth || 320
  const height = 180
  const regionCol = store.geojsonRegionCol
  const pair = regionPair.value

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  // Create a focused projection around the two highlighted regions
  const focusCollection: FeatureCollection = {
    type: 'FeatureCollection',
    features: [pair.featureA, pair.featureB]
  }

  const projection = d3.geoMercator().fitSize([width, height], focusCollection)

  // Expand bounds to show some context
  const contextProjection = d3.geoMercator().fitSize(
    [width * 0.5, height * 0.5],
    focusCollection
  )
  // Use the focused projection but zoom out a bit for context
  const scale = projection.scale()
  projection.scale(scale * 0.45)

  const path = d3.geoPath().projection(projection)

  // Draw all regions as background
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

  // Highlight region A
  svg
    .append('path')
    .datum(pair.featureA)
    .attr('d', path as any)
    .attr('fill', '#268bd2')
    .attr('stroke', '#1a6aa5')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.85)

  // Highlight region B
  svg
    .append('path')
    .datum(pair.featureB)
    .attr('d', path as any)
    .attr('fill', '#d76127')
    .attr('stroke', '#a84b1e')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.85)

  // Add labels for the two regions
  const centroidA = path.centroid(pair.featureA as any)
  const centroidB = path.centroid(pair.featureB as any)

  if (centroidA[0] && centroidA[1]) {
    svg
      .append('text')
      .attr('x', centroidA[0])
      .attr('y', centroidA[1])
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff')
      .attr('stroke', '#1a6aa5')
      .attr('stroke-width', 0.3)
      .text(formatNum(pair.valueA))
  }

  if (centroidB[0] && centroidB[1]) {
    svg
      .append('text')
      .attr('x', centroidB[0])
      .attr('y', centroidB[1])
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff')
      .attr('stroke', '#a84b1e')
      .attr('stroke-width', 0.3)
      .text(formatNum(pair.valueB))
  }
}

// Redraw map when the step or phase changes
watch(currentStep, () => {
  questionPhase.value = 'merge'
  nextTick(() => drawMiniMap())
})

function open() {
  currentStep.value = 0
  questionPhase.value = 'merge'
  if (modalEl.value) {
    modalInstance = new Modal(modalEl.value, { backdrop: 'static', keyboard: false })
    modalInstance.show()
    nextTick(() => drawMiniMap())
  }
}

function close() {
  modalInstance?.hide()
  emit('done')
}

// Track per-column votes from both questions
const mergeVote = ref<'sum' | 'average' | 'skip'>('skip')

function applyRecommendation(colIndex: number, vote: 'sum' | 'average') {
  if (vote === 'sum') {
    store.dataTable.fields[colIndex].recommendation = {
      type: 'area',
      reason:
        (store.dataTable.fields[colIndex].recommendation?.reason ?? '') +
        ' You confirmed this data is additive (extensive), so a cartogram is recommended.'
    }
  } else {
    store.dataTable.fields[colIndex].recommendation = {
      type: 'color',
      reason:
        (store.dataTable.fields[colIndex].recommendation?.reason ?? '') +
        ' You confirmed this data is not additive (intensive), so a choropleth is recommended.'
    }
  }
}

function advanceToNextColumn() {
  if (currentStep.value < props.columns.length - 1) {
    currentStep.value++
  } else {
    close()
  }
}

function answer(userAnswer: 'sum' | 'average' | 'skip') {
  if (!currentCol.value) return
  const colIndex = currentCol.value.index

  if (questionPhase.value === 'merge') {
    mergeVote.value = userAnswer
    // Move to the total question
    questionPhase.value = 'total'
    nextTick(() => drawMiniMapAll())
    return
  }

  // Phase 'total' — combine both votes
  // If both agree, apply that. If they disagree, prefer the total question (more holistic).
  // If either was skipped, use the other.
  const totalVote = userAnswer
  const finalVote =
    totalVote !== 'skip' ? totalVote : mergeVote.value !== 'skip' ? mergeVote.value : 'skip'

  if (finalVote !== 'skip') {
    applyRecommendation(colIndex, finalVote)
  }

  advanceToNextColumn()
}

// Draw a mini map highlighting ALL regions for the "total" question
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

  const projection = d3.geoMercator().fitSize([width - 16, height - 16], store.geojsonData)
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

defineExpose({ open })
</script>

<template>
  <div ref="modalEl" class="modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered">
      <div class="modal-content" v-if="currentCol">
        <div class="modal-header">
          <h5 class="modal-title">
            Sense-check: <strong>{{ currentCol.label }}</strong>
          </h5>
          <span class="badge text-bg-secondary ms-2">
            {{ currentStep + 1 }} / {{ columns.length }}
          </span>
        </div>
        <div class="modal-body">
          <p class="text-muted mb-2">
            Our algorithm suggests
            <strong>{{ algoSuggestion === 'area' ? 'cartogram (area)' : 'choropleth (color)' }}</strong>
            <span
              v-if="currentCol.recommendation.confidence != null"
              class="badge ms-1"
              :class="
                currentCol.recommendation.confidence >= 0.5
                  ? 'text-bg-success'
                  : currentCol.recommendation.confidence >= 0.2
                    ? 'text-bg-warning'
                    : 'text-bg-danger'
              "
            >
              {{ Math.round(currentCol.recommendation.confidence * 100) }}% fit
            </span>.
            Help us verify:
          </p>

          <div v-if="regionPair">
            <!-- Mini map -->
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
                    The sum — like total population, GDP, number of hospitals
                  </span>
                </button>
                <button class="btn btn-outline-primary text-start sense-btn" @click="answer('average')">
                  <span class="sense-btn-value">~{{ formatNum(avgValue) }}{{ currentUnit }}</span>
                  <span class="sense-btn-hint">
                    Somewhere between the two — like temperature, density, life expectancy
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
                    Summing doesn't make sense — e.g. temperature, life expectancy, percentages
                  </span>
                </button>
                <button class="btn btn-link text-muted text-start small" @click="answer('skip')">
                  Not sure — keep the algorithm's suggestion
                </button>
              </div>
            </template>
          </div>

          <div v-else class="text-muted">
            Not enough data to generate a question for this column.
            <button class="btn btn-link" @click="answer('skip')">Skip</button>
          </div>
        </div>
        <div class="modal-footer justify-content-between">
          <span class="text-muted small">
            Additive data (totals, counts) → cartogram &nbsp;|&nbsp;
            Non-additive data (rates, densities) → choropleth
          </span>
          <button class="btn btn-secondary btn-sm" @click="close()">Skip all</button>
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
