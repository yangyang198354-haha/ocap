<!-- MOD-123：认证申诉，自带房屋选择（Q-BL-21=A），自 Units.vue 原 51-71、168-195 行迁移 -->
<template>
  <div id="appeal" class="card">
    <h3 class="title">认证申诉</h3>
    <p class="muted">姓名与手机号未能通过清册核对时，可选择房屋、填写产权人名字并上传 1~5 份产权证明（jpg/png/pdf，单个不超过 10MB）提交申诉，由管理员审核。</p>
    <UnitCascader v-model="appealUnitId" />
    <div class="row" style="margin-top: 10px">
      <el-input v-model="appeal.ownerName" maxlength="64" placeholder="产权人名字" style="width: 220px" />
    </div>
    <div class="row" style="margin-top: 10px">
      <el-upload
        :show-file-list="false"
        :http-request="uploadProof"
        multiple
        :limit="5"
        accept=".jpg,.jpeg,.png,.pdf"
      >
        <el-button>上传产权证明</el-button>
      </el-upload>
      <span class="muted" v-if="appeal.attachmentIds.length">已上传 {{ appeal.attachmentIds.length }} 份（最多 5 份）</span>
      <el-button v-if="appeal.attachmentIds.length" size="small" @click="appeal.attachmentIds = []">清空</el-button>
      <el-button type="primary" :disabled="!appealUnitId" @click="submitAppeal">提交申诉</el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { attachmentApi, unitApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '../parts/UnitCascader.vue'

const store = useHousingStore()
const appealUnitId = ref(null)
const appeal = reactive({ ownerName: '', attachmentIds: [] })

async function uploadProof({ file }) {
  if (appeal.attachmentIds.length >= 5) return ElMessage.warning('最多上传 5 份产权证明')
  try {
    const uploaded = await attachmentApi.upload(file, 'APPEAL_PROOF')
    appeal.attachmentIds.push(uploaded.id)
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submitAppeal() {
  try {
    const ownerName = appeal.ownerName.trim()
    if (!ownerName) return ElMessage.warning('请输入产权人名字')
    if (!appeal.attachmentIds.length) return ElMessage.warning('请先上传产权证明')
    await unitApi.createAppeal({
      unit_id: appealUnitId.value,
      owner_name: ownerName,
      proof_ids: [...appeal.attachmentIds]
    })
    ElMessage.success('申诉已提交，等待管理员审核')
    appeal.attachmentIds = []
    await store.loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

// 认证页失败转来时，姓名由仓库带入（只带姓名，房屋需重新选择）
onMounted(() => {
  const name = store.consumePrefillOwnerName()
  if (name) appeal.ownerName = name
})
</script>
