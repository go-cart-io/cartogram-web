import { onMounted, onBeforeUnmount } from 'vue'

let disabled = false

/**
 * Composable to ask user confirmation before leaving or refreshing the page.
 */
export function useLeaveConfirm() {
  // Handle page refresh / closing tab
  const beforeUnloadHandler = (event: BeforeUnloadEvent) => {
    if (disabled) return
    event.preventDefault()
    event.returnValue = '' // Required for Chrome
  }

  onMounted(() => {
    window.addEventListener('beforeunload', beforeUnloadHandler)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', beforeUnloadHandler)
  })
}

export function disableLeaveConfirmOnce() {
  disabled = true
}
