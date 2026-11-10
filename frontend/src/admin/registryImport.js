// 清册导入前端辅助（MOD-036 / 对应 IFC-157、IFC-159）
import { errorText } from '@/shared/format'

// 导入最长 60 秒（后端软期限），客户端留 40 秒余量。
export const IMPORT_REQUEST_TIMEOUT_MS = 100000

export function importErrorMessage(error) {
  if (error?.code === 'ECONNABORTED' || error?.code === 'ETIMEDOUT') {
    return '导入超时，请缩小文件后重试'
  }
  return errorText(error)
}

export function formatImportResult(result) {
  if (!result) return ''
  return `共 ${result.rows_total} 行：新增 ${result.imported} 个专有部分、更新 ${result.updated} 个、` +
    `业主 ${result.owners_created ?? 0} 位，失败 ${result.failed} 行`
}

export function errorsCsv(errors) {
  const lines = [['行号', '字段', '原因'], ...(errors || []).map((e) => [e.row ?? '', e.field ?? '', e.reason ?? ''])]
  return lines
    .map((cells) => cells.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\r\n')
}

export function downloadText(filename, text, type = 'text/csv;charset=utf-8') {
  const blob = new Blob(['\ufeff' + text], { type })
  downloadBlob(blob, filename)
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
