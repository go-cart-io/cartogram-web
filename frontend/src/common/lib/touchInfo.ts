export default class TouchInfo {
  private touches = new Map<number, PointerEvent>()
  private touchIds = [] as Array<number>
  private thumbIndex = -1

  set(event: PointerEvent): void {
    if (this.touches.size >= 3 || event.pointerId === null) return // We only process 1-3 points

    this.touchIds.push(event.pointerId)
    this.touches.set(event.pointerId, event)

    switch (this.touches.size) {
      case 1:
        this.thumbIndex = event.pointerId
        return

      case 2:
        return // Just assume the first pointer as thumb

      case 3:
        const d01 = Math.hypot(
          this.getTouchId(this.touchIds[1]).pageY - this.getTouchId(this.touchIds[0]).pageY,
          this.getTouchId(this.touchIds[1]).pageX - this.getTouchId(this.touchIds[0]).pageX
        )
        const d12 = Math.hypot(
          this.getTouchId(this.touchIds[2]).pageY - this.getTouchId(this.touchIds[1]).pageY,
          this.getTouchId(this.touchIds[2]).pageX - this.getTouchId(this.touchIds[1]).pageX
        )
        const d20 = Math.hypot(
          this.getTouchId(this.touchIds[0]).pageY - this.getTouchId(this.touchIds[2]).pageY,
          this.getTouchId(this.touchIds[0]).pageX - this.getTouchId(this.touchIds[2]).pageX
        )

        // Assume two smallest distance is index and middle finger
        if (d01 <= d12 && d01 <= d20)
          // d01 is the smallest
          this.thumbIndex = this.getTouchId(this.touchIds[2]).pointerId
        else if (d01 > d12 && d12 <= d20)
          // d12 is the smallest
          this.thumbIndex = this.getTouchId(this.touchIds[0]).pointerId
        // d20 is the smallest
        else this.thumbIndex = this.getTouchId(this.touchIds[1]).pointerId
        return

      default:
        return
    }
  }

  update(event: PointerEvent): void {
    if (!this.touches.has(event.pointerId)) return
    this.touches.set(event.pointerId, event)
  }

  clear(event: PointerEvent): void {
    this.touches.delete(event.pointerId)
    this.touchIds = this.touchIds.filter((item) => item !== event.pointerId)
    if (this.thumbIndex === event.pointerId) this.thumbIndex = this.touchIds[0]
  }

  length(): number {
    return this.touches.size
  }

  getTouches(): Map<number, PointerEvent> {
    return this.touches
  }

  getTouchId(id: number): CustomPointerEvent {
    if (this.touches.has(id)) return this.touches.get(id)!

    return {
      pageX: -1,
      pageY: -1,
      pointerId: -1
    }
  }

  getAllPoints(ofsetX: number = 0, ofsetY: number = 0): number[][] {
    const points = [] as number[][]
    this.touches.forEach((touch) => {
      points.push([touch.pageX - ofsetX, touch.pageY - ofsetY])
    })

    return points
  }

  getMergedPoints(ofsetX = 0, ofsetY = 0): Array<any> {
    try {
      if (this.touches.size === 1) return [this.getThumb(ofsetX, ofsetY)]
      else if (this.touches.size > 1)
        return [this.getThumb(ofsetX, ofsetY), this.getOthers(ofsetX, ofsetY)]
    } catch (err) {
      console.error(err)
    }
    return []
  }

  getThumb(ofsetX = 0, ofsetY = 0): Array<number> {
    return [
      this.getTouchId(this.thumbIndex).pageX - ofsetX,
      this.getTouchId(this.thumbIndex).pageY - ofsetY
    ]
  }

  getOthers(ofsetX = 0, ofsetY = 0): Array<number> {
    if (this.touches.size < 2) return []

    let x = 0,
      y = 0

    this.touches.forEach((touch, key) => {
      if (key !== this.thumbIndex) {
        x += touch.pageX - ofsetX
        y += touch.pageY - ofsetY
      }
    })
    return [x / (this.touches.size - 1), y / (this.touches.size - 1)]
  }
}

interface CustomPointerEvent {
  pageX: number
  pageY: number
  pointerId: number
}
