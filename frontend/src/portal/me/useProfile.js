// MOD-122 / IFC-325：个人中心各页共用的资料加载（行为同原 Me.vue loadProfile）。
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { errorText } from '@/shared/format'

export function useProfile() {
  const profile = reactive({ nickname: '', gender: 0, birthday: null, phone: '', email: '', avatar_url: '' })

  async function loadProfile() {
    try {
      Object.assign(profile, await meApi.profile())
    } catch (e) {
      ElMessage.error(errorText(e))
    }
  }

  return { profile, loadProfile }
}
