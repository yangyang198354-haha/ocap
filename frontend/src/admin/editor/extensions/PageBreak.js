import { Node } from '@tiptap/core'

export const PageBreak = Node.create({
  name: 'pageBreak',
  group: 'block',
  atom: true,
  parseHTML() {
    return [{ tag: 'hr[data-page-break]' }]
  },
  renderHTML() {
    return ['hr', { 'data-page-break': 'true', class: 'rt-page-break' }]
  }
})
