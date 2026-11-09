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
