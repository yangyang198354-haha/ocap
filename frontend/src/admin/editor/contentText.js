// MOD-059：内容编辑页的中文提示文案（保存警告、400 定位、推送状态），与后端 IFC-169 / IFC-186 的枚举对应
const BLOCK_TYPE_TEXT = {
  paragraph: '段落', heading: '标题', bulletList: '无序列表', orderedList: '有序列表',
  listItem: '列表项', blockquote: '引用', horizontalRule: '分割线', hardBreak: '换行',
  image: '图片', video: '视频', pageBreak: '分页', text: '文本'
}

const REASON_TEXT = {
  COLOR: '颜色格式不支持',
  SIZE: '字号或行距超出范围',
  LINK: '链接地址无效',
  TYPE: '不支持的内容类型',
  MEDIA_ID: '外链图片请通过素材库插入',
  LEVEL: '标题级别已调整为 4 级',
  ATTR: '属性不合法',
  LIMIT: '内容超出限制'
}

export const PLATFORM_TEXT = { wechat_mp: '微信公众号', xiaohongshu: '小红书', toutiao: '今日头条' }

export const PUSH_STATUS_TEXT = {
  PENDING: '排队中', SENDING: '发送中', SAVED: '成功', FAILED: '失败',
  UNKNOWN: '结果未知', MANUAL_REQUIRED: '需人工粘贴'
}

const PUSH_ERROR_TEXT = {
  NO_CREDENTIALS: '未配置认证信息',
  AUTH_EXPIRED: '认证已失效，请重新认证',
  IP_NOT_WHITELISTED: '服务器出口 IP 未加入公众号 IP 白名单',
  TOKEN_BUSY: '令牌正在刷新，请稍后重试',
  UPSTREAM: '平台返回错误',
  NETWORK: '网络异常',
  COVER_REQUIRED: '内容中没有可用作封面的图片',
  IMAGE_UPLOAD_FAILED: '图片上传失败',
  INTERRUPTED: '任务中断',
  UNKNOWN: '结果未知，请到平台草稿箱核对后重试',
  INTERNAL: '内部错误'
}

const FEATURE_TEXT = {
  page_break: '分页', video: '视频', text_align: '对齐', text_color: '文字颜色',
  background_color: '背景色', font_size: '字号', line_height: '行距', blockquote: '引用',
  style_not_carried: '版式样式'
}

export function platformText(value) {
  return PLATFORM_TEXT[value] || value
}

export function pushStatusText(value) {
  return PUSH_STATUS_TEXT[value] || value
}

export function featureText(value) {
  return FEATURE_TEXT[value] || value
}

/** 失败原因：优先中文文案；平台/网络类错误附带（已脱敏的）原始说明。 */
export function pushErrorText(row) {
  const code = row?.error_code || ''
  const message = row?.error_message || ''
  if (!code) return message
  const text = PUSH_ERROR_TEXT[code]
  if (!text) return message || code
  if (['UPSTREAM', 'NETWORK', 'INTERNAL'].includes(code) && message) return `${text}：${message}`
  return text
}

export function blockPosition(blockIndex, blockType, doc) {
  if (blockIndex === null || blockIndex === undefined) return ''
  const type = blockType || doc?.content?.[blockIndex]?.type
  const label = BLOCK_TYPE_TEXT[type]
  return `第 ${blockIndex + 1} 个块${label ? `（${label}）` : ''}`
}

/** 保存响应的 warnings → 一行提示（最多列前 3 条位置 + 总数）；无警告返回空串。 */
export function warningsMessage(warnings, total, doc) {
  const count = total || (warnings ? warnings.length : 0)
  if (!count) return ''
  const parts = (warnings || []).slice(0, 3).map((item) => {
    const position = blockPosition(item.block_index, null, doc)
    return `${position}${position ? ' ' : ''}${REASON_TEXT[item.reason] || item.reason}`
  })
  return `已自动处理/忽略 ${count} 处不支持的格式：${parts.join('；')}${count > 3 ? ' 等' : ''}`
}

/** 400 CONTENT_INVALID_DOC → 带位置的提示。 */
export function invalidDocMessage(details, doc) {
  const position = blockPosition(details?.block_index, details?.block_type, doc)
  const reason = REASON_TEXT[details?.reason] || '正文格式不合法'
  return `正文${position ? ` ${position}` : ''}：${reason}`
}
