import type { Entry } from './interface'

/**
 * Tooltip contains helper functions for drawing and hiding the tooltip
 */
export default class Tooltip {
  /**
   * Draws a tooltip next the mouse cursor with the given content
   * @param event The current mouse event
   * @param content The new content of the tooltip
   */
  static draw(event: Event, content: string): void {
    let x, y
    if (event instanceof MouseEvent) {
      x = event.pageX
      y = event.pageY
    } else if (event instanceof TouchEvent) {
      x = event.changedTouches[0].pageX
      y = event.changedTouches[0].pageY
    }

    if (!x || !y) return
    document.getElementById('tooltip')!.innerHTML = content
    document.getElementById('tooltip')!.style.display = 'inline-block'
    document.getElementById('tooltip')!.style.left = x - 50 + 'px'
    document.getElementById('tooltip')!.style.top = y + 15 + 'px'
  }

  static drawWithEntries(
    event: MouseEvent,
    name: string,
    abbreviation: string,
    entries: Array<Entry>
  ): void {
    let content = '<b>' + name + ' (' + abbreviation + ')</b>'

    entries.forEach((entry) => {
      content +=
        '<br/><i>' + entry.name + ':</i> ' + entry.value.toLocaleString() + ' ' + entry.unit
    }, this)

    Tooltip.draw(event, content)
  }

  /**
   * Hides the tooltip from view
   */
  static hide(): void {
    document.getElementById('tooltip')!.style.display = 'none'
  }
}
