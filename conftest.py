"""pytest 公共配置：应用地址、页面对象和失败截图。"""

from __future__ import annotations

import os
from pathlib import Path
import re

import pytest
from playwright.sync_api import Page

from pages.ai_companion_page import AIChatApp


DEFAULT_APP_URL = "https://abc892813.streamlit.app/"
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


@pytest.fixture(scope="session")
def app_url() -> str:
    """优先读取环境变量，方便以后替换部署地址。"""
    return os.getenv("AI_COMPANION_URL", DEFAULT_APP_URL)


@pytest.fixture
def ai_app(page: Page, app_url: str, request: pytest.FixtureRequest) -> AIChatApp:
    """为每个测试提供独立的 AI 伴侣页面对象。"""
    app = AIChatApp(page=page, base_url=app_url)
    yield app

    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        ARTIFACTS_DIR.mkdir(exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.nodeid)
        screenshot_path = ARTIFACTS_DIR / f"{safe_name}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n失败截图已保存：{screenshot_path}")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """记录测试结果，让 ai_app 在测试失败后可以截图。"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
