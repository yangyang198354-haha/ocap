// GROUP_D：内容中心前端 API 契约（TC-UNIT-341~343）
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { admin, infoApi } from '@/shared/api'

const { http, adminHttp } = mocked

beforeEach(() => vi.clearAllMocks())

describe('内容中心管理端调用', () => {
  it('TC-UNIT-341 文章 CRUD 与发布路径/方法正确', async () => {
    adminHttp.get.mockResolvedValueOnce({ results: [] })
    await admin.contentPosts({ status: 'DRAFT', page: 1 })
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/content/posts',
      { params: { status: 'DRAFT', page: 1 } })

    adminHttp.post.mockResolvedValueOnce({ id: 1 })
    await admin.createContentPost({ title: 'x' })
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/content/posts', { title: 'x' })

    adminHttp.patch.mockResolvedValueOnce({})
    await admin.updateContentPost(1, { title: 'y' })
    expect(adminHttp.patch).toHaveBeenCalledWith('/admin/content/posts/1', { title: 'y' })

    adminHttp.post.mockResolvedValueOnce({})
    await admin.publishContentPost(1)
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/content/posts/1/publish', {})
  })

  it('TC-UNIT-342 素材/服务/平台/草稿路径正确', async () => {
    adminHttp.get.mockResolvedValueOnce({ results: [] })
    await admin.mediaList({ media_type: 'IMAGE' })
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/content/media',
      { params: { media_type: 'IMAGE' } })

    adminHttp.put.mockResolvedValueOnce({})
    await admin.saveContentService('LLM_DEEPSEEK', { secrets: { api_key: 'x' } })
    expect(adminHttp.put).toHaveBeenCalledWith('/admin/content/services/LLM_DEEPSEEK',
      { secrets: { api_key: 'x' } })

    adminHttp.post.mockResolvedValueOnce({ id: 3 })
    await admin.createPlatformAccount({ platform: 'wechat_mp', display_name: '公众号' })
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/content/platform-accounts',
      { platform: 'wechat_mp', display_name: '公众号' })

    adminHttp.post.mockResolvedValueOnce({ batch_id: 'b' })
    await admin.pushDrafts(9, [1, 2])
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/content/posts/9/drafts',
      { account_ids: [1, 2] })

    adminHttp.get.mockResolvedValueOnce({ blob: true })
    await admin.exportPack(9, 'xiaohongshu')
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/content/posts/9/export-pack',
      { params: { platform: 'xiaohongshu' }, responseType: 'blob' })
  })
})

describe('内容中心用户端调用', () => {
  it('TC-UNIT-343 列表与详情使用用户端 http 且 fmt 参数正确', async () => {
    http.get.mockResolvedValueOnce({ results: [] })
    await infoApi.list({ page: 1 })
    expect(http.get).toHaveBeenCalledWith('/info/posts', { params: { page: 1 } })

    http.get.mockResolvedValueOnce({ pages: [] })
    await infoApi.detail(5, 'blocks')
    expect(http.get).toHaveBeenCalledWith('/info/posts/5', { params: { fmt: 'blocks' } })
  })
})
