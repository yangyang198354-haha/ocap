// Independent visual preview: staggered binary streams behind the login content.
(() => {
  const canvas = document.querySelector('.matrix-rain')
  if (!canvas) return
  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) return

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
  const random = (min, max) => min + Math.random() * (max - min)
  const bit = () => (Math.random() < .5 ? '0' : '1')
  let width = 0
  let height = 0
  let fontSize = 26
  let rowHeight = 42
  let rows = 0
  let columns = []
  let lastFrame = 0
  let animationId = 0

  function makeColumn(index) {
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

  function resize() {
    const box = canvas.getBoundingClientRect()
    width = box.width
    height = box.height
    const ratio = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = Math.round(width * ratio)
    canvas.height = Math.round(height * ratio)
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    fontSize = width < 600 ? 19 : 26
    rowHeight = fontSize * 1.55
    rows = Math.ceil(height / rowHeight) + 1
    columns = Array.from({ length: Math.ceil(width / (fontSize + 10)) }, (_, i) => makeColumn(i))
    draw(0)
  }

  function draw(deltaSeconds) {
    ctx.clearRect(0, 0, width, height)
    ctx.font = `${fontSize}px Consolas, "Courier New", monospace`
    ctx.textBaseline = 'top'

    for (const column of columns) {
      // Quiet background bits flicker independently of the falling streams.
      for (let row = 0; row < rows; row++) {
        if (Math.random() < .012) column.ghosts[row] = bit()
        if ((row + Math.round(column.x)) % 3 === 0) continue
        ctx.fillStyle = `rgba(55, 221, 171, ${column.active ? .035 : .055})`
        ctx.fillText(column.ghosts[row], column.x, row * rowHeight)
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
        ctx.fillStyle = `rgba(${tail < 2 ? '126, 255, 205' : '57, 216, 165'}, ${alpha})`
        ctx.shadowColor = tail < 2 ? '#69f7c1' : 'transparent'
        ctx.shadowBlur = tail < 2 ? 7 : 0
        ctx.fillText(Math.random() < .14 ? bit() : column.ghosts[row], column.x, row * rowHeight)
      }
      ctx.shadowBlur = 0

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
    if (reducedMotion.matches) draw(0)
    else animationId = requestAnimationFrame(tick)
  }

  window.addEventListener('resize', resize)
  reducedMotion.addEventListener('change', syncMotion)
  resize()
  syncMotion()
})()
