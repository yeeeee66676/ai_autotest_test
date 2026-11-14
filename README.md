# AI 伴侣自动化测试

使用 pytest 和 Playwright 对线上 AI 伴侣进行端到端自动化测试。

测试地址：<https://abc892813.streamlit.app/>

## 环境准备

在 PowerShell 中进入项目目录：

```powershell
cd C:\Users\lks\PycharmProjects\PP1_autotest
```

安装 Python 依赖和 Chromium：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

## 运行测试

运行完整测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -vv
```

只运行不消耗 AI 额度的冒烟测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke -vv
```

只运行会调用 DeepSeek 的日期测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -m ai -vv
```

显示浏览器并观察操作过程：

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke --headed -vv
```

## 测试内容

- 检查应用页面和主要控件是否正常显示。
- 检查昵称与角色设定是否可以填写。
- 检查新建会话后会话标识是否发生变化。
- 真实调用一次 AI，验证回答中的上海日期是否正确。

完整测试会发起一次真实 DeepSeek 请求，请避免在短时间内频繁重复运行。

## 更换测试地址

无需修改代码，在 PowerShell 中设置环境变量：

```powershell
$env:AI_COMPANION_URL = "https://新的应用地址.streamlit.app/"
.\.venv\Scripts\python.exe -m pytest -m smoke -vv
```

## 失败截图

测试失败时会自动将截图保存到 `artifacts/` 目录。截图和测试缓存不会提交到 Git。

## 项目结构

```text
.
├── conftest.py
├── pages/
│   ├── __init__.py
│   └── ai_companion_page.py
├── tests/
│   └── test_ai_companion.py
├── artifacts/
│   └── .gitkeep
├── pytest.ini
├── requirements.txt
└── README.md
```
