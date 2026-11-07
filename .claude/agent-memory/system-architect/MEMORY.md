# system-architect 项目记忆 — ocap
## 已验证
## 用户偏好与禁止项
## 待验证
- [P-SA-001] 取微信官方服务端接口文档时，用 `developers.weixin.qq.com/miniprogram/dev/server/API/<分类>/<api_xxx>.md`（带 .md）可拿到干净正文；`/framework/open-ability/*.html` 页面正文过长，WebFetch 只返回导航 — 自记 2026-11-07 · 证据 本次 PHASE_03/04 的 WebFetch 结果
- [P-SA-002] 小程序"手机号快速验证组件"官方称仅向非个人且已认证主体开放并按次收费，设计上以短信验证码为基线、快速验证做可选开关，避免主体类型成为阻断 — 自记 2026-11-07 · 证据 搜索摘要（非官方原文），开发前复核；2026-11-07 官方 getphonenumber 页只写适用范围为小程序/小游戏，未写主体与收费
- [P-SA-003] 阿里云验证码短信模板：单变量须 4~6 位、双变量不可自定义，故有效期无法作为模板变量、只能写死在模板正文，设计上须用启动检查保证与配置的有效期一致；平台默认流控 1/分钟、5/小时、10/天与本项目 C-06 同值但窗口算法不同 — 自记 2026-11-07 · 证据 help.aliyun.com 验证码模板规范页与 message-rules 页
- [P-SA-004] 阿里云帮助页 WebFetch 偶发 "Socket is closed"，重试一次即可；api.aliyun.com 错误码页只给错误码名称、不给释义，释义需另找并标 [UNSOURCED] — 自记 2026-11-07 · 证据 本次 PHASE_03/04 WebFetch 结果
