<script>
export default {
  onLaunch() {
    // 登录态由 store/auth.js 在页面中按需恢复
  }
}
</script>

<style>
@import './theme/generated/themes.scss';
page { background: var(--bg); color: var(--text); font-size: 28rpx; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 24rpx; margin: 24rpx; box-shadow: var(--shadow); }
.title { font-size: 34rpx; font-weight: 650; margin-bottom: 16rpx; }
.muted { color: var(--muted); font-size: 24rpx; }
.row { display: flex; gap: 16rpx; align-items: center; flex-wrap: wrap; }
.btn { background: var(--accent-bg); color: var(--on-accent); border-radius: var(--radius-btn); }
.field { border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 16rpx; color: var(--text); background: var(--surface); min-height: 44px; box-sizing: border-box; }
.list-item { padding: 16rpx 0; border-bottom: 1px solid var(--line); }
.mt-16 { margin-top: 16rpx; }
.muted-gap { margin-left: 12rpx; }
.tag { display: inline-flex; align-items: center; gap: 8rpx; padding: 2rpx 16rpx; border-radius: 999px; font-size: 22rpx; color: var(--muted); background: var(--glass); }
.tag-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: currentColor; }
.tag.is-success { color: var(--success); background: var(--success-bg); }
.tag.is-warning { color: var(--warning); background: var(--warning-bg); }
.tag.is-danger { color: var(--danger); background: var(--danger-bg); }
.chip { display: inline-block; font-size: 22rpx; padding: 4rpx 20rpx; border-radius: 999px; border: 1px solid var(--line); background: var(--glass); }
.home-hero { position: relative; overflow: hidden; min-height: 300rpx; background: var(--hero); color: var(--on-hero); }
.home-hero-scan { display: none; }
.home-hero-main { position: relative; }
.home-greeting { font-size: 44rpx; font-weight: 700; margin: 8rpx 0; }
.home-meta { margin: 4rpx 0 16rpx; }
.hero .muted { color: var(--on-hero); }
.home-metrics { display: flex; flex-wrap: wrap; gap: 12rpx; }
.home-stats { display: grid; grid-template-columns: repeat(2, 1fr); }
.home-stats .card { margin: 12rpx 24rpx; }
.stat-value { font-size: 40rpx; font-weight: 700; margin-top: 8rpx; }
.home-quick { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16rpx; margin: 24rpx; }
.home-q { position: relative; display: flex; flex-direction: column; justify-content: flex-end; gap: 8rpx; min-height: 120rpx; padding: 20rpx; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); }
.home-q-key { display: none; font-size: 20rpx; color: var(--muted); font-family: var(--mono); }
.home-q-label { font-size: 28rpx; font-weight: 600; color: var(--text); }
.home-poll-title { font-size: 32rpx; line-height: 1.5; }
.res-card { display: block; }
.res-idx { font-size: 20rpx; color: var(--muted); font-family: var(--mono); margin-bottom: 8rpx; }
.res-title { font-size: 30rpx; font-weight: 650; }
.vote-bar { display: flex; height: 12rpx; overflow: hidden; border-radius: 999px; background: var(--glass); margin: 16rpx 0 8rpx; }
.vote-agree { height: 100%; background: var(--accent); }
.vote-disagree { height: 100%; background: var(--danger); }
.vote-abstain { height: 100%; background: var(--muted); opacity: 0.5; }
.vote-legend { display: flex; gap: 24rpx; font-size: 22rpx; color: var(--muted); }
.res-foot { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8rpx; font-size: 22rpx; color: var(--muted); margin-top: 12rpx; }
.mode-tag { margin-left: 8rpx; padding: 2rpx 14rpx; border-radius: 999px; border: 1px solid var(--line); font-size: 20rpx; }
.type-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; margin-bottom: 16rpx; }
.type-card { padding: 20rpx; min-height: 88rpx; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); }
.type-card.is-selected { border-color: var(--accent); }
.type-card-title { font-size: 28rpx; font-weight: 650; color: var(--text); }
.money-input { display: flex; align-items: center; gap: 16rpx; height: 128rpx; padding: 0 24rpx; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); }
.money-cur { font-size: 44rpx; font-weight: 700; color: var(--muted); }
.money-field { flex: 1; font-size: 56rpx; font-weight: 700; color: var(--text); font-family: var(--mono); }
.field-count { text-align: right; }
.claim-steps { margin-top: 16rpx; }
.theme-option { display: flex; flex-direction: column; align-items: center; gap: 8rpx; padding: 16rpx 20rpx; min-height: 88rpx; border: 2px solid var(--line); border-radius: var(--radius-md); background: var(--surface); }
.theme-option.is-selected { border-color: var(--accent); }
.theme-swatch { display: flex; width: 120rpx; height: 40rpx; border-radius: 8rpx; overflow: hidden; }
.theme-swatch view { flex: 1; }
.theme-name { font-size: 26rpx; color: var(--text); }
</style>
