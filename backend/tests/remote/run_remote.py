"""远程 HTTP E2E 入口（画像 P4-1）。不依赖 Django，只需要 requests。

用法（仓库根或任意目录均可）：
    OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD=<夹具密码> \
        python backend/tests/remote/run_remote.py [-v]
也可经 Django runner：
    (cd backend && OCAP_E2E_BASE_URL=… OCAP_E2E_PASSWORD=… python manage.py test tests.remote --pattern="remote_*.py" --settings=config.test_settings)

退出码：0 全部通过（含 skip）；1 有失败；2 缺少环境变量或目标不被允许（未发出任何请求）。
默认 `manage.py test` 与 CI 不会收集本目录（文件名不匹配 test*.py）。
"""
import os
import sys
import unittest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def main() -> int:
    from tests.remote.remote_client import Config, GuardError

    try:
        Config()
    except GuardError as exc:
        print(f"拒绝运行：{exc}", file=sys.stderr)
        return 2
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.remote.remote_cases")
    result = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
