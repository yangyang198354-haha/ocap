import { Node, mergeAttributes } from '@tiptap/core'

export const Video = Node.create({
  name: 'video',
  group: 'block',
  atom: true,
  addAttributes() {
    return {
      mediaId: { default: null },
      src: { default: null }
    }
  },
  parseHTML() {
    return [{ tag: 'video[data-media-id]' }]
  },
  renderHTML({ HTMLAttributes }) {
    return ['video', mergeAttributes(HTMLAttributes, { controls: 'true', 'data-media-id': HTMLAttributes.mediaId, src: HTMLAttributes.src })]
  }
})
