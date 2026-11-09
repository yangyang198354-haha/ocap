// 决议卡片的三段表决比例（与 frontend/src/shared/voteShare.js 同口径）：同意 / 反对 / 弃权占已投票数的百分比
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
