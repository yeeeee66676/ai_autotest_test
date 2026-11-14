"""封装 AI 伴侣页面操作，让测试代码只关注业务场景。"""

from __future__ import annotations

import re

from playwright.sync_api import FrameLocator, Locator, Page, expect


APP_IFRAME_SELECTOR = 'iframe[title="streamlitApp"]'
DEFAULT_STARTUP_TIMEOUT_MS = 120_000


class AIChatApp:
    """把页面控件和常用动作集中保存在一个类中。

    使用示例：

        def test_example(ai_app):
            ai_app.open()
            ai_app.set_profile("自动化测试", "回答简洁")
            before = ai_app.send_message("你好")
            reply = ai_app.wait_for_reply(before)
            assert reply.inner_text()
    """

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

        # Streamlit Cloud 会把应用放在 iframe 中，所有控件都要从 app_frame 查找。
        self.app_frame: FrameLocator = page.frame_locator(APP_IFRAME_SELECTOR)

        self.title = self.app_frame.get_by_role(
            "heading",
            name="AI 啥子伴侣",
            exact=True,
        )
        self.new_session_button = self.app_frame.get_by_role(
            "button",
            name="新建会话",
        )
        self.nickname_input = self.app_frame.get_by_role(
            "textbox",
            name="昵称",
        )
        self.character_input = self.app_frame.get_by_role(
            "textbox",
            name="角色设定",
        )
        self.chat_input = self.app_frame.get_by_test_id("stChatInputTextArea")
        self.send_button = self.app_frame.get_by_test_id(
            "stChatInputSubmitButton"
        )
        self.session_label = self.app_frame.get_by_text(
            "当前会话：",
            exact=False,
        ).first
        self.chat_messages: Locator = self.app_frame.locator(
            '[data-testid="stChatMessage"]'
        )

    def open(self, timeout_ms: int = DEFAULT_STARTUP_TIMEOUT_MS) -> "AIChatApp":
        """打开应用，并为冷启动留有足够时间。"""
        self.page.set_default_timeout(30_000)
        self.page.set_default_navigation_timeout(timeout_ms)
        self.page.goto(self.base_url, wait_until="domcontentloaded")

        try:
            expect(self.title).to_be_visible(timeout=timeout_ms)
        except AssertionError:
            # 免费版偶尔卡在冷启动页，刷新一次通常即可恢复。
            self.page.reload(wait_until="domcontentloaded")
            expect(self.title).to_be_visible(timeout=timeout_ms)

        return self

    def set_profile(self, nickname: str, character: str) -> None:
        """填写昵称和角色设定，并触发 Streamlit 刷新。"""
        self.nickname_input.fill(nickname)
        self.nickname_input.press("Tab")
        expect(self.nickname_input).to_have_value(nickname)

        self.character_input.fill(character)
        self.character_input.press("Tab")
        expect(self.character_input).to_have_value(character)

    def current_session_text(self) -> str:
        """返回当前会话标签中的完整文字。"""
        expect(self.session_label).to_be_visible()
        return self.session_label.inner_text()

    def start_new_session(self) -> str:
        """点击新建会话，并返回新的会话标签文字。"""
        previous_text = self.current_session_text()
        self.new_session_button.click()

        # 新会话会生成不同时间，因此标签文字应发生变化。
        expect(self.session_label).not_to_have_text(
            previous_text,
            timeout=30_000,
        )
        return self.current_session_text()

    def message_count(self) -> int:
        """返回页面中已有的聊天消息数量。"""
        return self.chat_messages.count()

    def send_message(self, text: str) -> int:
        """发送消息，并返回发送前的消息数量。

        返回值用于 wait_for_reply，帮助测试等待本次新回复，
        而不是误把以前的聊天记录当成新回复。
        """
        previous_count = self.message_count()

        self.chat_input.fill(text)
        expect(self.send_button).to_be_enabled()
        self.send_button.click()
        return previous_count

    def wait_for_reply(
        self,
        previous_count: int,
        timeout_ms: int = DEFAULT_STARTUP_TIMEOUT_MS,
    ) -> Locator:
        """等待用户消息和 AI 回复各增加一条，并返回回复气泡。"""
        expected_count = previous_count + 2
        expect(self.chat_messages).to_have_count(
            expected_count,
            timeout=timeout_ms,
        )
        reply = self.chat_messages.nth(expected_count - 1)
        reply_content = reply.locator('[data-testid="stChatMessageContent"]')

        # 回复气泡会先出现头像，正文稍后才流式写入；等待正文非空再返回。
        expect(reply_content).to_contain_text(
            re.compile(r"\S"),
            timeout=timeout_ms,
        )

        # 应用使用 submit_mode="disable"：输入框重新启用表示流式回复已经结束。
        expect(self.chat_input).to_be_enabled(timeout=timeout_ms)
        return reply_content
