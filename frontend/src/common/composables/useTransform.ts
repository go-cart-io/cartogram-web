import { ref } from 'vue'
import * as d3 from 'd3'

import TouchInfo from '../lib/touchInfo'
import * as numberUtil from '../lib/numberUtil'
import * as matrixUtil from '../lib/matrixUtil'

export const useTransform = (panelID: string) => {
  const DELAY_THRESHOLD = 300
  const touchInfo = new TouchInfo()

  const stateLastMove = ref(0)
  const stateTouchLenght = ref(0)
  const stateAffineScale = ref([1, 1]) // Keep track of scale for scaling grid easily

  let pointerangle: number | boolean, // (A)
    pointerposition: number[] | null, // (B)
    pointerdistance: number | boolean // (C)
  let lastTouch = 0
  let affineMatrix = matrixUtil.getOriginalMatrix()
  let gridScaleNiceNumber = 1

  // https://observablehq.com/@d3/multitouch
  function onPointerdown(event: any) {
    touchInfo.set(event)
    stateTouchLenght.value = touchInfo.length()

    const now = new Date().getTime()
    const timesince = now - lastTouch
    if (touchInfo.length() === 1 && timesince < DELAY_THRESHOLD && timesince > 0) {
      // Double tap
      reset()
    } else {
      const t = touchInfo.getMergedPoints()
      if (t.length > 0) {
        pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
        pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
        pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
      }
    }

    lastTouch = new Date().getTime()
    stateLastMove.value = lastTouch
  }

  function onPointerup(event: any) {
    document.getElementById(panelID)!.releasePointerCapture(event.pointerId)
    touchInfo.clear(event)
    stateTouchLenght.value = touchInfo.length()

    snapToBetterNumber()
    if (touchInfo.length() === 0) {
      pointerposition = null // signals mouse up
    } else {
      const t = touchInfo.getMergedPoints()
      if (t.length > 0) {
        pointerangle = t.length > 1 && Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (A)
        pointerposition = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0] // (B)
        pointerdistance = t.length > 1 && Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0]) // (C)
      }
    }
  }

  function onPointermove(event: any, isLockRatio: boolean) {
    touchInfo.update(event)
    if (touchInfo.length() < 1 || touchInfo.length() > 3 || !pointerposition) return

    // Capture pointer so gesture can be beyond the panel
    document.getElementById('vg-tooltip-element')?.classList.remove('visible')
    document.getElementById(panelID)!.setPointerCapture(event.pointerId)

    const t = touchInfo.getMergedPoints()
    let matrix = matrixUtil.getOriginalMatrix()
    let angle = 0
    const position = [0, 0]
    const scale = [1, 1]
    const now = new Date().getTime()

    // Order should be rotate, scale, translate
    // https://gamedev.stackexchange.com/questions/16719/what-is-the-correct-order-to-multiply-scale-rotation-and-translation-matrices-f
    if (t.length > 1 && (touchInfo.length() === 3 || (touchInfo.length() === 2 && !isLockRatio))) {
      // rotate
      const pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
      if (pointerangle && typeof pointerangle === 'number') angle = pointerangle2 - pointerangle
      else angle = 0
      pointerangle = pointerangle2
      matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getRotateMatrix(angle))

      // stretch
      const pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
      if (pointerdistance && typeof pointerdistance === 'number')
        scale[0] = pointerdistance2 / pointerdistance
      else scale[0] = 0
      stateAffineScale.value[0] *= scale[0]
      pointerdistance = pointerdistance2
      if (scale[0] !== 0) {
        matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getRotateMatrix(pointerangle))
        matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getScaleMatrix(scale[0], 1))
        matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getRotateMatrix(-pointerangle))
      }
    } else if (t.length > 1) {
      // (B) rotate
      if (pointerangle && typeof pointerangle === 'number') {
        const pointerangle2 = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0])
        angle = pointerangle2 - pointerangle
        pointerangle = pointerangle2
        matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getRotateMatrix(angle))
      }
      // (C) scale
      if (pointerdistance && typeof pointerdistance === 'number') {
        const pointerdistance2 = Math.hypot(t[1][1] - t[0][1], t[1][0] - t[0][0])
        scale[0] = pointerdistance2 / pointerdistance
        scale[1] = pointerdistance2 / pointerdistance
        stateAffineScale.value[0] *= scale[0]
        stateAffineScale.value[1] *= scale[1]
        pointerdistance = pointerdistance2
        if (scale[0] !== 0 && scale[1] !== 0)
          matrix = matrixUtil.multiplyMatrix(matrix, matrixUtil.getScaleMatrix(scale[0], scale[1]))
      }
    }

    const timesince = now - lastTouch
    if (touchInfo.length() > 1 || (touchInfo.length() === 1 && timesince > DELAY_THRESHOLD)) {
      // (A) translate
      const pointerposition2 = [d3.mean(t, (d) => d[0]) || 0, d3.mean(t, (d) => d[1]) || 0]
      position[0] = pointerposition2[0] - pointerposition[0]
      position[1] = pointerposition2[1] - pointerposition[1]
      pointerposition = pointerposition2
      matrix = matrixUtil.multiplyMatrix(
        matrix,
        matrixUtil.getTranslateMatrix(position[0], position[1])
      )
    }

    _apply(matrix, affineMatrix)

    stateLastMove.value = new Date().getTime()
  }

  function onWheel(event: any, isLockRatio: boolean, stretchDirection: string) {
    let matrix: Array<Array<number>> = []
    if (event.shiftKey) {
      matrix = matrixUtil.getRotateMatrix(event.wheelDelta / 1000)
    } else {
      const scale = 1 + event.wheelDelta / 1000
      let scales

      if (isLockRatio) {
        scales = [scale, scale]
      } else if (stretchDirection === 'x') {
        scales = [scale, 1]
      } else {
        scales = [1, scale]
      }

      stateAffineScale.value[0] *= scales[0]
      stateAffineScale.value[1] *= scales[1]
      matrix = matrixUtil.getScaleMatrix(scales[0], scales[1])
    }
    _apply(matrix, affineMatrix)
  }

  function applyCurrent() {
    _apply(affineMatrix, matrixUtil.getOriginalMatrix())
  }

  function _apply(matrix1: Array<Array<number>>, matrix2: Array<Array<number>>) {
    affineMatrix = matrixUtil.multiplyMatrix(matrix1, matrix2)

    d3.selectAll('#' + panelID + ' g.root').attr(
      'transform',
      'matrix(' +
        affineMatrix[0][0] +
        ' ' +
        affineMatrix[1][0] +
        ' ' +
        affineMatrix[0][1] +
        ' ' +
        affineMatrix[1][1] +
        ' ' +
        affineMatrix[0][2] +
        ' ' +
        affineMatrix[1][2] +
        ')'
    )
  }

  function reset() {
    affineMatrix = matrixUtil.getOriginalMatrix()
    stateAffineScale.value = [1, 1]
    _apply(affineMatrix, affineMatrix)
  }

  function setGridScaleNiceNumber(value: number) {
    gridScaleNiceNumber = value
  }

  function snapToBetterNumber() {
    const value = gridScaleNiceNumber / (stateAffineScale.value[0] * stateAffineScale.value[1])
    if (value === 0) return

    const [scaleNiceNumber, scalePowerOf10] = numberUtil.findNearestNiceNumber(value)
    const targetValue = scaleNiceNumber * Math.pow(10, scalePowerOf10)
    const adjustedScale = Math.sqrt(value / targetValue)

    stateAffineScale.value[0] *= adjustedScale
    stateAffineScale.value[1] *= adjustedScale
    const matrix = matrixUtil.getScaleMatrix(adjustedScale, adjustedScale)
    _apply(matrix, affineMatrix)
  }

  return {
    stateLastMove,
    stateTouchLenght,
    stateAffineScale,
    touchInfo,
    onPointerdown,
    onPointerup,
    onPointermove,
    onWheel,
    applyCurrent,
    reset,
    setGridScaleNiceNumber,
    snapToBetterNumber
  }
}
