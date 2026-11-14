"""远程 HTTP E2E 套件（画像 P4-1）：只经公开入口发 HTTP 请求，部署后由 GROUP_E2 在用户授权下执行。

默认 `manage.py test` 不收集本目录（文件名为 remote_*.py / run_remote.py，不匹配 test*.py）。
入口：见 run_remote.py 文件头。
"""
