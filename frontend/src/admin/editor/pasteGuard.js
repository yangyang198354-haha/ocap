// MOD-059 / IFC-242：粘贴守卫，在 DOMParser 解析出的文档上处理（不用正则改 HTML），不做网络请求、不转存图片（ADR-062）
import { toHexColor } from './colors.js'

const REMOVE_TAGS = 'script,style,iframe,object,embed,audio,video'
const COLOR_PROPS = new Set(['color', 'background-color'])

function normalizeStyleAttr(element) {
  const raw = element.getAttribute('style')
  if (!raw) return
  const kept = []
  for (const declaration of raw.split(';')) {
    const index = declaration.indexOf(':')
    if (index < 0) continue
    const prop = declaration.slice(0, index).trim().toLowerCase()
    const value = declaration.slice(index + 1).trim()
    if (COLOR_PROPS.has(prop)) {
      // 无法归一化的颜色声明直接删除，文字保留
      const hex = toHexColor(value)
      if (hex) kept.push(`${prop}: ${hex}`)
    } else {
      kept.push(`${prop}: ${value}`)
    }
  }
  if (kept.length) element.setAttribute('style', kept.join('; '))
  else element.removeAttribute('style')
}

/** 返回过滤后的 HTML 与被丢弃的外链图片数量。 */
export function guardPastedHtml(html) {
  const parsed = new DOMParser().parseFromString(String(html ?? ''), 'text/html')
  let droppedImages = 0
  // 视频只能经素材库插入：保留编辑器自身输出（带 data-media-id）的 <video>，其余移除
  parsed.body.querySelectorAll(REMOVE_TAGS).forEach((node) => {
    if (node.tagName === 'VIDEO' && node.getAttribute('data-media-id')) return
    node.remove()
  })
  // 没有编辑器自身 Image 节点输出的 data-media-id 的 <img>（外链、data:、blob:）一律移除并计数
  parsed.body.querySelectorAll('img').forEach((img) => {
    if (!img.getAttribute('data-media-id')) {
      img.remove()
      droppedImages += 1
    }
  })
  parsed.body.querySelectorAll('[style]').forEach(normalizeStyleAttr)
  return { html: parsed.body.innerHTML, droppedImages }
}
