// 决议卡片的三段表决比例：同意 / 反对 / 弃权占已投票数的百分比（接口未返回应投总数，故不含“未表决”）
export function voteShare(counts) {
  const agree = Number(counts?.agree) || 0
  const disagree = Number(counts?.disagree) || 0
  const abstain = Number(counts?.abstain) || 0
  const total = agree + disagree + abstain
  const pct = (n) => (total ? (n / total) * 100 : 0)
  return {
    agree, disagree, abstain, total,
    agreePct: pct(agree), disagreePct: pct(disagree), abstainPct: pct(abstain)
  }
}

// 决议卡片参与进度（MOD-149 / REQ-FUNC-245）：分母为应参与人数 expected（含待绑定席位，与通过判定同口径），余量留白；
// expected 为 0 时 empty=true（页面显示“暂无表决人”且不画条）；百分比整数取整
export function participationShare(item) {
  const counts = item?.vote_counts
  const agree = Number(counts?.agree) || 0
  const disagree = Number(counts?.disagree) || 0
  const abstain = Number(counts?.abstain) || 0
  const part = item?.participation
  const voted = part && part.voted != null ? Number(part.voted) || 0 : agree + disagree + abstain
  const expected = Number(part?.expected) || 0
  if (expected <= 0) {
    return { voted, expected: 0, pct: 0, agree, disagree, abstain, agreePct: 0, disagreePct: 0, abstainPct: 0, empty: true }
  }
  const of = (n) => Math.min(100, (n / expected) * 100)
  return {
    voted, expected, pct: Math.min(100, Math.round((voted / expected) * 100)), agree, disagree, abstain,
    agreePct: of(agree), disagreePct: of(disagree), abstainPct: of(abstain), empty: false
  }
}

// 距截止时间的剩余天 / 时 / 分；无截止时间返回 null
export function remaining(deadline, now = Date.now()) {
  if (!deadline) return null
  const ts = new Date(deadline).getTime()
  if (Number.isNaN(ts)) return null
  const ms = ts - now
  if (ms <= 0) return { expired: true, days: 0, hours: 0, minutes: 0 }
  const minutesTotal = Math.floor(ms / 60000)
  return {
    expired: false,
    days: Math.floor(minutesTotal / 1440),
    hours: Math.floor((minutesTotal % 1440) / 60),
    minutes: minutesTotal % 60
  }
}
