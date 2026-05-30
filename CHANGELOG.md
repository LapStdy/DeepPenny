# 更新日志

## v1.4（2026-05-30）

### 新增

- **MiSans 字体渲染** — 内置小米 MiSans 字体（Regular + Bold），通过 `QFontDatabase.addApplicationFont` 加载，替换系统默认字体，消除像素感，文字更圆润清晰
- **字体渲染优化** — 设置 `PreferNoHinting` 关闭字体微调、`PreferAntialias` 开启抗锯齿，在深色半透明背景上呈现更平滑的视觉效果
- **吸附指示器视觉引导** — 拖拽悬浮窗时目标区域即时显示实线边框引导，进入吸附范围后边框高亮，提供清晰的拖拽落点反馈

### 变更

- **「余额」改为「账户余额」** — 悬浮窗文本更清晰直观，涉及初始文本、刷新占位、刷新成功 3 处
- **缩小吸附判定范围** — `_snap_threshold` 从 60 降至 30，吸附判定范围从 ≈80px 缩小至 ≈50px，减少误触
- **吸附指示器状态分离** — `SnapZoneIndicator` 新增 `active`/`inactive` 双状态：未进入范围时边框/背景几乎透明（alpha 10/2），进入范围后高亮（alpha 80/20）；文字始终保持清晰；边框从虚线改为实线

### 文档

- **README.md 同步更新** — 项目结构新增 `fonts/` 目录，功能特性补充字体优化及吸附指示器说明，技术实现新增吸附机制章节

---

## v1.3（2026-05-30）

### 修复

- **修复 API Key 保存竞态丢失** — 当 keyring 不可用时，`save_config` 先写入不含 key 的 `config.json` 再调用 `save_api_key`，避免 API Key 被擦除
- **修复 `setup_logger` 重复添加 Handler** — 多次调用时重复添加 file_handler 和 console_handler 导致日志重复输出，添加 `if logger.handlers` 保护

### 变更

- **删除 `secure_config.py` 死代码** — 该文件函数不完整（`get_api_key` 截断）且功能与 `utils/secure_storage.py` 完全重复，删除

### 优化

- **置顶定时器降频** — `_ensure_topmost` 定时器从 200ms 放宽至 3s 作为兜底（前台钩子为主力），减少 93% 不必要的 `SetWindowPos` 调用；诊断日志降级为 DEBUG
- **SVG 颜色替换加固** — 从简单字符串替换升级为正则匹配 `fill`/`stroke` 属性，支持 `#333` / `#333333` / `#33333333` 等多种颜色格式
- **配置文件原子写入** — 使用临时文件 + `replace()` 原子操作，防止写入过程中崩溃导致 `config.json` 损坏
- **绝对路径支持** — `config.json` 路径从相对路径改为基于 `__file__` 的绝对路径，不受工作目录影响
- **SnapZoneIndicator 资源释放** — 添加 `cleanup()` 方法，提供销毁 indicator 窗口的入口
- **DeepSeekAPI 构造优化** — 提供 API Key 时自动构建 HTTP 客户端，避免首次请求时的延迟初始化

### 测试

- **修复 3 个失败测试** — 添加缺失的 `import httpx`、修复 `test_close` 断言（构造时自动建 client）、移除无效的 guard 逻辑
- **清理未使用的导入** — 移除 `test_core.py` 中未使用的 `patch` 导入

---

## v1.2（2026-05-30）

### 新增

- **依赖分类管理** — `install_deps.bat` 将组件明确分为**必装**（PyQt6、httpx）和**可选**（keyring、pytest、psutil）两类
- **可选组件交互式安装** — 未安装的可选组件逐一询问用户（Y/N），按需安装或跳过
- **多镜像源自动切换** — 预设清华、阿里云、中科大、豆瓣 4 个镜像源，依次尝试；镜像连接超时（15 秒）自动切换至下一个；全部不可用时回退官方源（pypi.org）

### 变更

- **重写 `install_deps.bat`** — 全中文交互界面，4 步安装流程（检测必装 → 询问可选 → 验证导入 → 清理临时文件）
- **更新 README.md** — 「安装依赖」节反映脚本新行为；「依赖项」表格拆分为必装组件和可选组件两个子表；项目结构描述同步更新

### 修复

- **修复闪退问题** — 将文件换行符从 Unix LF（`\n`）转换为 Windows CRLF（`\r\n`），解决双击脚本时 cmd.exe 解析失败导致的闪退和中文乱码

### 优化

- **提高安装可靠性** — 安装完毕自动验证所有组件的导入状态，失败时给出明确提示
- **安装后自动清理** — 清除 pip 缓存及 `%TEMP%`、`C:\Windows\Temp` 下的 pip 临时文件
