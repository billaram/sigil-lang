<script setup lang="ts">
defineProps<{
  bindings: Record<string, unknown>
}>()

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return 'none'
  if (typeof val === 'string') {
    if (val.startsWith(':')) return val
    return `"${val}"`
  }
  if (typeof val === 'number' || typeof val === 'boolean') return String(val)
  if (Array.isArray(val)) return `[${val.map(formatValue).join(', ')}]`
  if (typeof val === 'object') {
    const entries = Object.entries(val as Record<string, unknown>)
    return `{ ${entries.map(([k, v]) => `${k}: ${formatValue(v)}`).join(', ')} }`
  }
  return String(val)
}

function valueClass(val: unknown): string {
  if (val === null || val === undefined) return 'text-slate-400'
  if (typeof val === 'string') {
    if (val.startsWith(':')) return 'text-violet-600 dark:text-violet-400'
    return 'text-green-600 dark:text-green-400'
  }
  if (typeof val === 'number') return 'text-orange-600 dark:text-orange-400'
  if (typeof val === 'boolean') return 'text-blue-600 dark:text-blue-400'
  return 'text-slate-700 dark:text-slate-300'
}
</script>

<template>
  <div class="h-full overflow-auto p-3">
    <template v-if="Object.keys(bindings).length">
      <table class="w-full text-sm font-mono">
        <tbody>
          <tr
            v-for="(val, key) in bindings"
            :key="String(key)"
            class="border-b border-slate-100 dark:border-slate-800"
          >
            <td class="py-1 pr-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{{ key }}</td>
            <td :class="['py-1', valueClass(val)]">{{ formatValue(val) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
    <div v-else class="text-slate-400 dark:text-slate-500 italic text-sm">
      No bindings. Run a program to see variable values.
    </div>
  </div>
</template>
