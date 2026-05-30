# DeepPenny — 实时显示 DeepSeek API 余额

一个基于 PyQt6 的 Windows 桌面小工具，在任务栏附近显示悬浮窗，定时刷新 DeepSeek API 账户余额，让你随时掌握账户消费状态。

---

## 功能特性

- **实时余额展示** — 定时查询 DeepSeek API 账户余额并显示在悬浮窗上
- **MiSans 字体渲染** — 内置小米 MiSans 字体，配合 `PreferNoHinting + PreferAntialias` 渲染策略，文字边缘平滑无像素感
- **智能置顶** — 通过 Win32 `SetWinEventHook` 前台事件钩子为主力 + 3s 兜底定时器双重保障，悬浮窗始终保持在任务栏上方，即使点击「开始」菜单或「任务视图」也不会被遮挡
- **吸附到任务栏** — 拖拽移动窗口时目标区域即时显示实线边框引导，进入吸附范围后边框高亮，松开鼠标自动吸附到任务栏右边缘
- **安全存储** — API Key 加密存储到 Windows 凭据管理器
- **可配置刷新间隔** — 10–3600 秒可调
- **错误处理** — 完善的异常捕获与自动重试

---

## 使用方法

本程序提供两种运行方式，任选其一即可。

### 方式一：直接使用 EXE（推荐，无需安装 Python）

1. 下载 `DeepPenny.exe`
2. 双击运行 `DeepPenny.exe`
3. 首次运行时自动弹出设置窗口，输入你的 [DeepSeek API Key](https://platform.deepseek.com/api_keys)
4. 点击「保存」，浮窗开始显示余额

> 关闭浮窗（点击 `✕`）即可退出程序。API Key 会安全存储在 Windows 凭据管理器中，下次启动无需重新输入。

---

### 方式二：使用 Python 运行（适合开发者）

如果你已安装 Python，可以直接从源码运行：

#### 1. 环境要求

- Python 3.9 或更高版本
- Windows 操作系统

#### 2. 安装依赖

直接运行一键安装脚本（推荐）：

```bash
install_deps.bat
```

脚本特性：

- **必装组件** — PyQt6（GUI 框架）、httpx（HTTP 客户端），缺失时**自动安装**
- **可选组件** — keyring（凭据存储）、pytest（测试框架）、psutil（性能测试），缺失时**逐一询问**是否安装
- **多镜像源** — 预设清华、阿里云、中科大、豆瓣 4 个镜像源，按序尝试；连接超时（15 秒）自动切换；全部不可用时回退官方源
- **自动验证** — 安装完毕自动验证所有组件能否正常导入
- **自动清理** — 安装后清理 `pip` 缓存和临时文件

#### 3. 运行程序

```bash
python main.py
```

#### 4. 运行测试（可选）

```bash
pytest tests/ -v
```

---

## 配置文件

程序运行后会在根目录生成 `config.json`（已加入 `.gitignore`），结构如下：

```json
{
  "api_key": "",
  "refresh_interval": 60,
  "snap_offset": 300
}
```

| 字段 | 说明 | 默认值 |
|---|---|---|
| `api_key` | DeepSeek API Key（优先存入系统凭据管理器） | 空 |
| `refresh_interval` | 余额刷新间隔（秒） | 60 |
| `snap_offset` | 吸附时距任务栏右边缘的偏移量（像素） | 300 |

---

## 技术实现

### 窗口置顶机制

悬浮窗使用双重置顶策略确保不会被任务栏覆盖：

1. **WinEventHook 事件监听（主力）** — 注册 `EVENT_SYSTEM_FOREGROUND` 钩子，前台窗口切换时立即置顶
2. **3s 兜底定时器** — 每 3 秒调用一次 `SetWindowPos(HWND_TOPMOST)`，防止钩子遗漏的场景

通过 Z-order 验证日志可以确认 `WS_EX_TOPMOST` 标志始终为 `True`。

### 性能基线

| 指标 | 数值 |
|:----|:----:|
| CPU 增量 | < 0.5%（实测接近 0%） |
| SetWindowPos 平均延迟 | ~50 µs |
| 每秒总 CPU 开销 | ~0.3 ms |

可通过以下命令在本地复现性能测试：

```bash
python benchmark_topmost.py
```

测试结果会输出到终端并保存到 `benchmark_report.txt`，DEBUG 级别的日志输出到 `benchmark_debug.log`。

---

## 项目结构

```
DeepPenny/
├── main.py                      # 入口
├── requirements.txt             # Python 依赖
├── install_deps.bat             # 一键依赖安装（多镜像源切换 + 必装/可选交互）
├── benchmark_topmost.py         # 置顶定时器性能测试
├── fonts/
│   ├── MiSans-Regular.ttf       # 内置字体（小米 MiSans）
│   └── MiSans-Bold.ttf
├── ui/
│   ├── floating_window.py       # 悬浮窗主窗口 + Win32 置顶实现
│   ├── settings_dialog.py       # 设置对话框
│   └── snap_manager.py          # 吸附逻辑
├── api/
│   └── deepseek_api.py          # DeepSeek API 调用
├── utils/
│   ├── secure_storage.py        # API Key 安全存储
│   └── logger.py                # 日志配置
├── resources/
│   ├── styles.qss               # QSS 样式表
│   └── icons/                   # SVG 图标
└── tests/
    └── test_core.py             # 单元测试
```

---

## 如何获取 API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
2. 登录后点击「创建 API Key」
3. 复制生成的 Key（以 `sk-` 开头）
4. 粘贴到程序的设置对话框中

---

## 依赖项

### 必装组件（程序运行必需）

| 包 | 用途 |
|---|---|
| [PyQt6](https://pypi.org/project/PyQt6/) | 桌面 GUI 框架 |
| [httpx](https://pypi.org/project/httpx/) | HTTP 客户端，调用 DeepSeek API |

### 可选组件（按需安装）

| 包 | 用途 | 安装后可用的功能 |
|---|---|---|
| [keyring](https://pypi.org/project/keyring/) | API Key 安全存储到系统凭据管理器 | 加密保存密钥，替代明文 config |
| [pytest](https://pypi.org/project/pytest/) | Python 测试框架 | 运行 `pytest tests/ -v` |
| [psutil](https://pypi.org/project/psutil/) | 系统资源监控 | 运行 `benchmark_topmost.py` |

---

## 许可证

本项目基于 MIT License 开源，详见 [LICENSE.txt](LICENSE.txt)。
