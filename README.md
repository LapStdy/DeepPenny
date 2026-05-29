# DeepPenny — 实时显示 DeepSeek API 余额

一个基于 PyQt6 的 Windows 桌面小工具，会在任务栏附近显示悬浮窗，定时刷新 DeepSeek API 账户余额，让你随时掌握账户消费状态。

---

## 功能特性

- 实时查询并显示 DeepSeek API 余额
- 悬浮窗可吸附到任务栏，融入桌面不碍眼
- 拖拽移动窗口，松开自动检测吸附
- API Key 安全存储到系统凭据管理器（Windows 凭据管理器）
- 可配置刷新间隔（10–3600 秒）
- 完善的错误处理与自动重试

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

```bash
pip install -r requirements.txt
```

如果下载速度较慢，可以指定国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

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

## 如何获取 API Key

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys)
2. 登录后点击「创建 API Key」
3. 复制生成的 Key（以 `sk-` 开头）
4. 粘贴到程序的设置对话框中

---

## 依赖项

| 包 | 用途 |
|---|---|
| [PyQt6](https://pypi.org/project/PyQt6/) | 桌面 GUI 框架 |
| [httpx](https://pypi.org/project/httpx/) | HTTP 客户端，调用 DeepSeek API |
| [keyring](https://pypi.org/project/keyring/) | API Key 安全存储到系统凭据管理器 |

---

## 许可证

本项目基于 MIT License 开源，详见 [LICENSE.txt](LICENSE.txt)。
