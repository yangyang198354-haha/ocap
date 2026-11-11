<template>
  <div class="rich-editor">
    <Toolbar :editor="editor" @pick-media="$emit('pick-media', $event)"
             @page-break="insertPageBreak" @request-link="requestLink" />
    <editor-content :editor="editor" class="re-body" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import Image from '@tiptap/extension-image'
import { TextStyle, Color, BackgroundColor, FontSize, LineHeight } from '@tiptap/extension-text-style'
import { ElMessage } from 'element-plus'
import Toolbar from './Toolbar.vue'
import { Video } from './extensions/Video.js'
import { PageBreak } from './extensions/PageBreak.js'
import { toHexColor } from './colors.js'
import { guardPastedHtml } from './pasteGuard.js'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ type: 'doc', content: [] }) },
  mediaUrls: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'pick-media', 'paste-dropped'])

// 解析 HTML 时把函数式颜色归一化为十六进制，无法归一化则不设置该属性（ADR-062）
function colorAttribute(name, cssProp, cssName) {
  return {
    default: null,
    parseHTML: (element) => toHexColor(String(element.style[cssProp] || '').replace(/['"]+/g, '')),
    renderHTML: (attributes) => (attributes[name] ? { style: `${cssName}: ${attributes[name]}` } : {})
  }
}
const SafeColor = Color.extend({
  addGlobalAttributes() {
    return [{ types: this.options.types, attributes: { color: colorAttribute('color', 'color', 'color') } }]
  }
})
const SafeBackgroundColor = BackgroundColor.extend({
  addGlobalAttributes() {
    return [{
      types: this.options.types,
      attributes: { backgroundColor: colorAttribute('backgroundColor', 'backgroundColor', 'background-color') }
    }]
  }
})

function transformPastedHTML(html) {
  const result = guardPastedHtml(html)
  if (result.droppedImages) emit('paste-dropped', { images: result.droppedImages })
  return result.html
}

const MediaImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      mediaId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-media-id'),
        renderHTML: (attributes) => (attributes.mediaId ? { 'data-media-id': attributes.mediaId } : {})
      }
    }
  }
})

const editor = useEditor({
  content: withMedia(props.modelValue),
  editable: !props.disabled,
  extensions: [
    StarterKit.configure({ code: false, codeBlock: false, heading: { levels: [1, 2, 3, 4] } }),
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    TextStyle,
    SafeColor,
    SafeBackgroundColor,
    FontSize,
    LineHeight,
    MediaImage.configure({ inline: false, allowBase64: false }),
    Video,
    PageBreak
  ],
  editorProps: { transformPastedHTML },
  onUpdate: ({ editor: instance }) => emit('update:modelValue', instance.getJSON())
})

function withMedia(node) {
  if (!node || typeof node !== 'object') return node
  const copy = { ...node }
  if ((copy.type === 'image' || copy.type === 'video') && copy.attrs?.mediaId) {
    copy.attrs = { ...copy.attrs, src: copy.attrs.src || props.mediaUrls[copy.attrs.mediaId] || '' }
  }
  if (Array.isArray(copy.content)) copy.content = copy.content.map(withMedia)
  return copy
}

function syncMediaSrc() {
  if (!editor.value) return
  const { state, view } = editor.value
  const updates = []
  state.doc.descendants((node, pos) => {
    if (node.type.name !== 'image' && node.type.name !== 'video') return
    const mediaId = node.attrs.mediaId
    const src = mediaId ? props.mediaUrls[mediaId] || '' : ''
    if (src && node.attrs.src !== src) updates.push([pos, node, src])
  })
  if (!updates.length) return
  let tr = state.tr
  for (const [pos, node, src] of updates) {
    tr = tr.setNodeMarkup(pos, undefined, { ...node.attrs, src })
  }
  view.dispatch(tr)
}

watch(() => props.mediaUrls, syncMediaSrc, { deep: true })

watch(() => props.disabled, (value) => editor.value?.setEditable(!value))
watch(() => props.modelValue, (value) => {
  if (!editor.value) return
  const current = JSON.stringify(editor.value.getJSON())
  if (JSON.stringify(value || {}) !== current) {
    editor.value.commands.setContent(withMedia(value || { type: 'doc', content: [] }), false)
    syncMediaSrc()
  }
}, { deep: true })

function insertMedia(kind, mediaId, url) {
  if (!editor.value) return
  if (kind === 'video') {
    editor.value.chain().focus().insertContent({ type: 'video', attrs: { mediaId, src: url } }).run()
  } else {
    editor.value.chain().focus().setImage({ src: url, mediaId }).run()
  }
}
function insertPageBreak() {
  editor.value?.chain().focus().insertContent({ type: 'pageBreak' }).run()
}
function clearFormat() {
  editor.value?.chain().focus().unsetAllMarks().clearNodes().run()
}
function requestLink() {
  const url = window.prompt('输入链接地址（http/https/mailto/tel）')
  if (url === null) return
  if (!/^(https?:\/\/|mailto:|tel:)/i.test(url)) {
    ElMessage.error('网址无效')
    return
  }
  editor.value?.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

defineExpose({ insertMedia, insertPageBreak, clearFormat })
onBeforeUnmount(() => editor.value?.destroy())
</script>
