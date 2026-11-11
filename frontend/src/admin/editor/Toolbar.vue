<template>
  <div class="re-toolbar">
    <el-button-group>
      <el-button size="small" :type="isActive('bold') ? 'primary' : ''" @click="run('toggleBold')">B</el-button>
      <el-button size="small" :type="isActive('italic') ? 'primary' : ''" @click="run('toggleItalic')">I</el-button>
      <el-button size="small" :type="isActive('underline') ? 'primary' : ''" @click="run('toggleUnderline')">U</el-button>
      <el-button size="small" :type="isActive('strike') ? 'primary' : ''" @click="run('toggleStrike')">S</el-button>
    </el-button-group>
    <el-select :model-value="heading" size="small" style="width: 90px" @change="setHeading">
      <el-option label="正文" :value="0" />
      <el-option v-for="n in 4" :key="n" :label="`标题${n}`" :value="n" />
    </el-select>
    <el-button-group>
      <el-button v-for="align in aligns" :key="align" size="small"
                 :type="isActive({ textAlign: align }) ? 'primary' : ''"
                 @click="run('setTextAlign', align)">{{ alignLabel(align) }}</el-button>
    </el-button-group>
    <el-button-group>
      <el-button size="small" @click="run('toggleBulletList')">无序</el-button>
      <el-button size="small" @click="run('toggleOrderedList')">有序</el-button>
      <el-button size="small" @click="run('toggleBlockquote')">引用</el-button>
      <el-button size="small" @click="run('setHorizontalRule')">分割线</el-button>
    </el-button-group>
    <el-input v-model="color" size="small" style="width: 90px" placeholder="文字色" @change="setColor" />
    <el-input v-model="background" size="small" style="width: 90px" placeholder="背景色" @change="setBackground" />
    <el-input v-model.number="fontSize" size="small" style="width: 80px" placeholder="字号" @change="setFontSize" />
    <el-input v-model.number="lineHeight" size="small" style="width: 80px" placeholder="行距" @change="setLineHeight" />
    <el-button-group>
      <el-button size="small" @click="run('undo')">撤销</el-button>
      <el-button size="small" @click="run('redo')">重做</el-button>
      <el-button size="small" @click="run('unsetAllMarks')">清除格式</el-button>
    </el-button-group>
    <el-button-group>
      <el-button size="small" @click="$emit('pick-media', 'image')">图片</el-button>
      <el-button size="small" @click="$emit('pick-media', 'video')">视频</el-button>
      <el-button size="small" @click="$emit('page-break')">分页</el-button>
      <el-button size="small" @click="$emit('request-link')">链接</el-button>
    </el-button-group>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({ editor: { type: Object, default: null } })
defineEmits(['pick-media', 'page-break', 'request-link'])

const aligns = ['left', 'center', 'right', 'justify']
const color = ref('')
const background = ref('')
const fontSize = ref('')
const lineHeight = ref('')

const heading = computed(() => {
  if (!props.editor) return 0
  for (let n = 1; n <= 4; n += 1) if (props.editor.isActive('heading', { level: n })) return n
  return 0
})

watch(() => props.editor, (editor) => {
  if (!editor) return
  color.value = editor.getAttributes('textStyle').color || ''
  background.value = editor.getAttributes('textStyle').backgroundColor || ''
  fontSize.value = (editor.getAttributes('textStyle').fontSize || '').replace('px', '')
  lineHeight.value = editor.getAttributes('textStyle').lineHeight || ''
})

function isActive(name) {
  return props.editor ? props.editor.isActive(name) : false
}
function run(command, arg) {
  if (!props.editor) return
  const chain = props.editor.chain().focus()
  chain[command](arg).run()
}
function alignLabel(align) {
  return { left: '左', center: '中', right: '右', justify: '两端' }[align]
}
function setHeading(level) {
  if (!props.editor) return
  const chain = props.editor.chain().focus()
  if (!level) chain.setParagraph().run()
  else chain.toggleHeading({ level }).run()
}
function setColor(value) {
  if (!props.editor || !value) return
  props.editor.chain().focus().setColor(value).run()
}
function setBackground(value) {
  if (!props.editor || !value) return
  props.editor.chain().focus().setBackgroundColor(value).run()
}
function setFontSize(value) {
  if (!props.editor || !value) return
  props.editor.chain().focus().setFontSize(`${value}px`).run()
}
function setLineHeight(value) {
  if (!props.editor || !value) return
  props.editor.chain().focus().setLineHeight(value).run()
}
</script>
