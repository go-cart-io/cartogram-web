export default class TouchInfo {
  touches = {} as { [key: string]: any }
  length = 0
  thumbIndex = -1

  set(event: TouchEvent | MouseEvent): void {
    if (event instanceof TouchEvent) this.setTouches(event.touches)
    else this.setPointer(event)
  }

  setPointer(event: MouseEvent) {
    this.updatePointer(event)
    this.thumbIndex = 0
  }

  setTouches(touchlist: TouchList): void {
    this.updateTouches(touchlist)

    switch (touchlist.length) {
      case 0:
        this.thumbIndex = -1
        return

      case 1:
        this.thumbIndex = touchlist[0].identifier
        return

      case 2:
        if (
          this.thumbIndex === touchlist[0].identifier ||
          this.thumbIndex === touchlist[1].identifier
        ) {
          return // same thumb
        }
        this.thumbIndex = touchlist[0].identifier
        return

      case 3:
        let d01 = Math.hypot(
          touchlist[1].pageY - touchlist[0].pageY,
          touchlist[1].pageX - touchlist[0].pageX
        )
        let d12 = Math.hypot(
          touchlist[2].pageY - touchlist[1].pageY,
          touchlist[2].pageX - touchlist[1].pageX
        )
        let d20 = Math.hypot(
          touchlist[0].pageY - touchlist[2].pageY,
          touchlist[0].pageX - touchlist[2].pageX
        )

        // Assume two smallest distance is index and middle finger
        if (d01 <= d12 && d01 <= d20)
          // d01 is the smallest
          this.thumbIndex = touchlist[2].identifier
        else if (d01 > d12 && d12 <= d20)
          // d12 is the smallest
          this.thumbIndex = touchlist[0].identifier
        // d20 is the smallest
        else this.thumbIndex = touchlist[1].identifier
        return

      default:
        return
    }
  }

  update(event: TouchEvent | MouseEvent): void {
    if (event instanceof TouchEvent) this.updateTouches(event.touches)
    else this.updatePointer(event)
  }

  updatePointer(event: MouseEvent) {
    this.touches = { 0: event }
    this.length = 1
  }

  updateTouches(touchlist: TouchList): void {
    this.touches = {}
    this.length = touchlist.length
    for (let i = 0; i < touchlist.length; i++) {
      this.touches[touchlist[i].identifier] = touchlist[i]
    }
  }

  clear(event: any) {
    if (event instanceof TouchEvent) this.setTouches(event.touches)
    else this.clearPointer()
  }

  clearPointer() {
    this.touches = {}
    this.length = 0
    this.thumbIndex = 0
  }

  getPoints(): Array<any> {
    try {
      if (this.length === 1) return [this.getThumb()]
      else if (this.length > 1) return [this.getThumb(), this.getOthers()]
    } catch (err) {}
    return []
  }

  getThumb(ofsetX = 0, ofsetY = 0): Array<number> {
    return [
      this.touches[this.thumbIndex].pageX - ofsetX,
      this.touches[this.thumbIndex].pageY - ofsetY
    ]
  }

  getOthers(ofsetX = 0, ofsetY = 0): Array<number> {
    if (this.length < 2) return []

    let x = 0,
      y = 0
    for (const identifier in this.touches) {
      if (identifier === this.thumbIndex.toString()) continue
      x += this.touches[identifier].pageX - ofsetX
      y += this.touches[identifier].pageY - ofsetY
    }
    return [x / (this.length - 1), y / (this.length - 1)]
  }
}
