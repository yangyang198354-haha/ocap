// @dcloudio/uni-app 生命周期钩子的最小桩（真实实现依赖 uni 运行时，本机不可执行）。
// onShow / onLoad 在组件 setup 中同步登记，由测试用 runLifecycle() 触发，便于控制时序。
const hooks = { show: [], load: [] }

export function onShow(fn) {
  hooks.show.push(fn)
}

export function onLoad(fn) {
  hooks.load.push(fn)
}

/** 触发已登记的生命周期钩子并清空；query 作为 onLoad 参数 */
export async function runLifecycle(query = {}) {
  const loads = hooks.load.splice(0)
  const shows = hooks.show.splice(0)
  for (const fn of loads) await fn(query)
  for (const fn of shows) await fn()
}

export function resetLifecycle() {
  hooks.show.length = 0
  hooks.load.length = 0
}
