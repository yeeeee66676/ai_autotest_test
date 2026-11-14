"""AI 伴侣线上功能的 pytest + Playwright 自动化测试。"""

from datetime import datetime
import re
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from pages.ai_companion_page import AIChatApp


PROFILE_NICKNAME = "自动化测试"
PROFILE_CHARACTER = "回答简洁，只回答用户询问的信息"
AI_ERROR_MESSAGES = (
    "AI 服务暂时不可用",
    "DeepSeek API 密钥无效",
    "DeepSeek 请求失败",
    "无法连接 DeepSeek",
    "连接 DeepSeek 超时",
)


@pytest.mark.smoke
def test_app_loads(ai_app: AIChatApp) -> None:
    """应用和主要控件应该能在浏览器中正常显示。"""
    ai_app.open()

    expect(ai_app.title).to_be_visible()
    expect(ai_app.new_session_button).to_be_visible()
    expect(ai_app.nickname_input).to_be_visible()
    expect(ai_app.character_input).to_be_visible()
    expect(ai_app.chat_input).to_be_visible()
    expect(ai_app.chat_input).to_be_editable()
    expect(ai_app.session_label).to_contain_text("当前会话：")


@pytest.mark.smoke
def test_profile_can_be_set(ai_app: AIChatApp) -> None:
    """修改昵称和角色后，输入框应保留新内容。"""
    ai_app.open()
    ai_app.set_profile(PROFILE_NICKNAME, PROFILE_CHARACTER)

    expect(ai_app.nickname_input).to_have_value(PROFILE_NICKNAME)
    expect(ai_app.character_input).to_have_value(PROFILE_CHARACTER)


@pytest.mark.smoke
def test_new_session_changes_session_id(ai_app: AIChatApp) -> None:
    """点击新建会话后，页面中的会话时间应发生变化。"""
    ai_app.open()
    old_session = ai_app.current_session_text()
    new_session = ai_app.start_new_session()

    assert new_session != old_session, "新建会话后会话标识没有变化"
    expect(ai_app.session_label).to_have_text(new_session)


@pytest.mark.ai
def test_ai_answers_with_correct_shanghai_date(ai_app: AIChatApp) -> None:
    """真实请求一次 AI，确认当天日期使用上海时区且没有服务错误。"""
    ai_app.open()
    ai_app.set_profile(PROFILE_NICKNAME, PROFILE_CHARACTER)

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    before_count = ai_app.send_message("今天几号？请直接回答日期和星期。")
    reply = ai_app.wait_for_reply(before_count)

    # 兼容模型常见的三种日期写法，避免因格式稍有不同而误报失败。
    possible_dates = (
        f"{today.year}年{today.month}月{today.day}日",
        f"{today.year:04d}-{today.month:02d}-{today.day:02d}",
        f"{today.year}/{today.month:02d}/{today.day:02d}",
    )
    date_pattern = re.compile("|".join(re.escape(text) for text in possible_dates))

    try:
        # 流式回复会逐字出现，等待日期真正出现后再读取正文。
        expect(reply).to_contain_text(date_pattern, timeout=30_000)
    except AssertionError:
        # 不在这里中断，下面会给出包含实际回复内容的清晰错误信息。
        pass

    reply_text = reply.inner_text()
    assert reply_text.strip(), "AI 回复为空"
    assert not any(message in reply_text for message in AI_ERROR_MESSAGES), (
        f"AI 返回了错误提示：{reply_text}"
    )
    assert any(date_text in reply_text for date_text in possible_dates), (
        f"AI 没有回答正确日期 {today.isoformat()}，实际回答：{reply_text}"
    )
