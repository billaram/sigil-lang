import { ref, watchEffect } from 'vue'

const dark = ref(false)

function init() {
  const stored = localStorage.getItem('sigil-dark-mode')
  if (stored !== null) {
    dark.value = stored === 'true'
  } else {
    dark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  applyClass()
}

function applyClass() {
  document.documentElement.classList.toggle('dark', dark.value)
}

function toggle() {
  dark.value = !dark.value
  localStorage.setItem('sigil-dark-mode', String(dark.value))
  applyClass()
}

export function useDarkMode() {
  init()
  return { dark, toggle }
}
