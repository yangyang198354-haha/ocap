<!-- MOD-137：认证产权（只做产权认证；同住人申请已迁至 UnitsApplications，ADR-134） -->
<template>
  <div>
    <RegistryMatchPanel />
    <div class="card">
      <h3 class="title">认证产权</h3>
      <p class="muted">逐级选择你的专有部分，输入您本人的姓名后点击"认证产权"。</p>
      <UnitCascader v-model="pickedUnitId" />
      <div class="row" style="margin-top: 10px">
        <span>您本人的姓名</span>
        <el-input v-model="certifyName" maxlength="64" placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）" style="width: 360px" aria-label="您本人的姓名" />
      </div>
      <div class="row" style="margin-top: 10px">
        <el-button type="primary" :disabled="!pickedUnitId" @click="certify">认证产权</el-button>
      </div>
      <p class="muted">您本人的姓名与当前手机号和清册登记的同一位业主一致时可立即认证为产权业主。不一致或没有手机号时，请改用"认证申诉"（输入姓名并上传产权证明，无手机号也可申诉）。</p>
      <p class="muted">如需申请成为同住人，请前往<router-link to="/units/applications">「我的同住人申请」</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import { ROLE_LABELS } from '@/shared/labels'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '../parts/UnitCascader.vue'
import RegistryMatchPanel from '../parts/RegistryMatchPanel.vue'

const router = useRouter()
const auth = useAuthStore()
const store = useHousingStore()
const pickedUnitId = ref(null)
const certifyName = ref('')

async function certify() {
  const name = certifyName.value.trim()
  if (!name) return ElMessage.warning('请输入姓名')
  try {
    const result = await unitApi.certify(pickedUnitId.value, name)
    ElMessage.success(`认证成功，身份：${ROLE_LABELS[result.role] || result.role}`)
    await auth.fetchMe()
    await store.refresh()
  } catch (e) {
    if (e?.code === 'OWNER_NOT_MATCHED') {
      // 只把姓名带入申诉页，不带房屋（UnitCascader 无法回显所选楼栋/单元，OQ-B03）；不显示任何清册信息（AC-201-02）
      store.setPrefillOwnerName(name)
      ElMessage.warning('姓名与手机号未能通过核对，请上传产权证明提交申诉')
      router.push('/units/appeal')
      return
    }
    ElMessage.error(errorText(e))
  }
}
</script>
