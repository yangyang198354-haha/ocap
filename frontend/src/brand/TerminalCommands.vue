<template>
  <div class="auth-terminal-window">
    <div class="auth-terminal-viewport">
      <div ref="track" class="auth-terminal-track">
        <p
          v-for="row in rows"
          :key="row.id"
          class="auth-terminal-line"
          :class="{ 'is-typing': row.id === activeId }"
        >&gt; {{ row.id === activeId ? row.command.slice(0, typed) : row.command }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'

const commands = [
  'boot cyber@hongfengling', 'init community-console', 'scan neighborhood nodes',
  'load resident directory', 'mount service gateway', 'sync community status',
  'check identity channel', 'link established [OK]', 'open sign-in station',
]
const track = ref(null)
const rows = shallowRef([])
const activeId = ref(-1)
const typed = ref(0)
const motion = window.matchMedia?.('(prefers-reduced-motion: reduce)')
let timer
let slide
let nextId = 0

function rowLimit() {
  return Number(getComputedStyle(track.value).getPropertyValue('--terminal-rows')) || 5
}

function stop() {
  clearTimeout(timer)
  slide?.cancel()
}

function startLine() {
  const id = nextId++
  const command = commands[id % commands.length]
  const limit = rowLimit()
  const previousCount = rows.value.length
  rows.value = [...rows.value, { id, command }].slice(-limit)
  activeId.value = id
  typed.value = 0

  if (previousCount >= limit) {
    slide = track.value.animate?.(
      [{ transform: 'translateY(var(--terminal-line-height))' }, { transform: 'translateY(0)' }],
      { duration: 340, easing: 'cubic-bezier(.2,.75,.3,1)' },
    )
  }

  function typeNext() {
    const character = command[typed.value]
    typed.value += 1
    if (typed.value < command.length) {
      timer = setTimeout(typeNext, character === ' ' ? 90 : 43)
    } else {
      timer = setTimeout(startLine, 660)
    }
  }
  timer = setTimeout(typeNext, previousCount >= limit ? 250 : 100)
}

function restart() {
  stop()
  activeId.value = -1
  nextId = 0
  const isStatic = !motion || motion.matches || document.hidden
  rows.value = isStatic ? commands.slice(0, rowLimit()).map((command, id) => ({ id, command })) : []
  if (!isStatic) startLine()
}

onMounted(() => {
  motion?.addEventListener?.('change', restart)
  document.addEventListener('visibilitychange', restart)
  restart()
})
onBeforeUnmount(() => {
  stop()
  motion?.removeEventListener?.('change', restart)
  document.removeEventListener('visibilitychange', restart)
})
</script>
