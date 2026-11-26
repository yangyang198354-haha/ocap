// Binary streams for the terminal login background. Stops cleanly on unmount.
export function startTerminalMatrix(canvas) {
  if (!canvas) return () => {}
  const motion = typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: true, addEventListener() {}, removeEventListener() {} }
  const random = (min, max) => min + Math.random() * (max - min)
  const bit = () => (Math.random() < .5 ? '0' : '1')
  let context
  let columns = []
  let width = 0
  let height = 0
  let rows = 0
  let fontSize = 26
  let rowHeight = 40
  let lastFrame = 0
  let animationId = 0

  function createColumn(index) {
    return {
      x: index * (fontSize + 10) + random(-5, 5),
      head: random(-rows, rows),
      speed: random(2.1, 7.4),
      trail: Math.round(random(7, 19)),
      strength: random(.55, 1),
      active: Math.random() < .76,
      ghosts: Array.from({ length: rows }, bit)
    }
  }

  function draw(deltaSeconds) {
    if (!context) return
    context.clearRect(0, 0, width, height)
    context.font = `${fontSize}px Consolas, "Courier New", monospace`
    context.textBaseline = 'top'
    for (const column of columns) {
      for (let row = 0; row < rows; row++) {
        if (Math.random() < .012) column.ghosts[row] = bit()
        if ((row + Math.round(column.x)) % 3 === 0) continue
        context.fillStyle = `rgba(55, 221, 171, ${column.active ? .035 : .055})`
        context.fillText(column.ghosts[row], column.x, row * rowHeight)
      }
      if (!column.active) {
        if (Math.random() < deltaSeconds * .18) column.active = true
        continue
      }
      column.head += column.speed * deltaSeconds
      const headRow = Math.floor(column.head)
      for (let tail = column.trail; tail >= 0; tail--) {
        const row = headRow - tail
        if (row < 0 || row >= rows) continue
        const fade = 1 - tail / (column.trail + 1)
        const alpha = (.035 + .29 * fade * fade) * column.strength
        context.fillStyle = `rgba(${tail < 2 ? '126, 255, 205' : '57, 216, 165'}, ${alpha})`
        context.shadowColor = tail < 2 ? '#69f7c1' : 'transparent'
        context.shadowBlur = tail < 2 ? 7 : 0
        context.fillText(Math.random() < .14 ? bit() : column.ghosts[row], column.x, row * rowHeight)
      }
      context.shadowBlur = 0
      if (column.head - column.trail > rows) {
        column.head = random(-rows * .65, -2)
        column.speed = random(2.1, 7.4)
        column.trail = Math.round(random(7, 19))
        column.strength = random(.55, 1)
        column.active = Math.random() < .82
      }
    }
  }

  function tick(now) {
    if (now - lastFrame >= 55) {
      draw(Math.min((now - lastFrame) / 1000, .12))
      lastFrame = now
    }
    animationId = requestAnimationFrame(tick)
  }

  function syncMotion() {
    cancelAnimationFrame(animationId)
    lastFrame = performance.now()
    if (motion.matches || document.documentElement.dataset.perf === 'low') draw(0)
    else animationId = requestAnimationFrame(tick)
  }

  function resize() {
    const box = canvas.getBoundingClientRect()
    if (!box.width || !box.height) return
    if (!context) context = canvas.getContext('2d')
    if (!context) return
    width = box.width
    height = box.height
    const ratio = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = Math.round(width * ratio)
    canvas.height = Math.round(height * ratio)
    context.setTransform(ratio, 0, 0, ratio, 0, 0)
    fontSize = width < 600 ? 19 : 26
    rowHeight = fontSize * 1.55
    rows = Math.ceil(height / rowHeight) + 1
    columns = Array.from({ length: Math.ceil(width / (fontSize + 10)) }, (_, i) => createColumn(i))
    draw(0)
  }

  resize()
  window.addEventListener('resize', resize)
  motion.addEventListener('change', syncMotion)
  syncMotion()
  return () => {
    cancelAnimationFrame(animationId)
    window.removeEventListener('resize', resize)
    motion.removeEventListener('change', syncMotion)
  }
}
