---
name: "朗泰 LungTic"
description: "可核验的 4D 肺癌智能辅助工作台"
colors:
  brand-blue: "#1E88E5"
  brand-blue-hover: "#42A5F5"
  brand-blue-pressed: "#1565C0"
  action-blue-hover: "#0D47A1"
  hero-midnight: "#07111F"
  hero-panel: "#101B2B"
  content-bg: "#F5F7FA"
  surface: "#FFFFFF"
  ink: "#1E293B"
  ink-secondary: "#52647B"
  border: "#DCE5EE"
  success: "#087A55"
  warning: "#9A5B00"
  danger: "#C43845"
typography:
  display:
    fontFamily: "Noto Sans SC, Source Han Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "clamp(2.75rem, 5.2vw, 5.5rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Noto Sans SC, Source Han Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "clamp(2rem, 3.6vw, 3.75rem)"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Noto Sans SC, Source Han Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Noto Sans SC, Source Han Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  control: "8px"
  surface: "12px"
  media: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.brand-blue-pressed}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "14px 22px"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "13px 20px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
---

# Design System: 朗泰 LungTic

## 1. Overview

**Creative North Star: “临床大工作台”**

官网像在安静、受控的阅片室里拉开一块真实工作台：深海军蓝首屏把视线压到 LungTic 的界面证据上，明亮内容区再逐步解释工作流、TICI 与研发边界。视觉不是“AI 科幻”，而是精密仪器与临床软件的组合——冷静、可信、前沿。

管理台使用同一品牌蓝，但回到高可读的浅色操作环境。信息密度来自清楚的层级、表格和状态，不来自卡片堆叠。所有动效必须表达状态；所有医学影像必须来自真实软件截图或明确标注的合成数据。

**Key Characteristics:**

- 深蓝沉浸首屏，白色与冷灰承载长文内容。
- 大画幅真实工作台是主要视觉证据，不以装饰图形替代产品。
- 8px 间距体系、8–16px 克制圆角、清晰的功能色。
- 官网节奏宽松而有戏剧性；管理台紧凑、稳定、可审计。
- 所有能力状态、风险提示与发布结果同时使用文字、图标和颜色表达。

## 2. Colors

色彩从现有 LungTic 软件提取：品牌蓝代表可操作的主动作，海军蓝代表影像工作区，白色与冷灰负责临床信息阅读。

### Primary

- **朗泰成像蓝**：品牌识别色，用于焦点环、当前状态和非文字图形。
- **清亮反馈蓝**：只用于小面积数据高亮，不承载白色小号正文。
- **深压反馈蓝**：高对比主动作底色，确保白色按钮文字达到 WCAG AA。
- **动作悬停蓝**：主动作悬停与按下反馈，保持足够文字对比。

### Secondary

- **阅片室午夜蓝**：官网首屏与影像舞台的主背景。
- **设备面板蓝黑**：真实工作台框架、工具栏和深色面板。

### Neutral

- **临床冷灰**：官网明亮内容区与管理台应用背景。
- **检查台白**：表单、表格、发布面板和可读内容表面。
- **深墨蓝**：浅色背景上的主文字与标题。
- **注释蓝灰**：辅助说明与元数据；不得用于关键正文。
- **结构冷线**：分隔线、表格行和输入边界，避免在每个容器上制造“幽灵卡片”。

### Named Rules

**The Evidence Blue Rule.** 品牌蓝只能标记“可操作、当前、进行中”，不得作为无意义装饰铺满页面。

**The Two Rooms Rule.** 官网首屏属于深色阅片室，内容与管理台属于明亮检查台；不要把整站做成单一暗黑 SaaS 模板。

## 3. Typography

**Display Font:** Noto Sans SC（本地托管，Source Han Sans SC 与系统中文无衬线回退）

**Body Font:** Noto Sans SC（本地托管，Source Han Sans SC 与系统中文无衬线回退）

**Label/Mono Font:** 系统等宽字体仅用于哈希、版本号、文件大小和任务 ID。

**Character:** 单一中文无衬线家族提供临床清晰度，靠字重、行距和尺度建立戏剧性。它像设备铭牌与专业软件，不像杂志，也不用等宽字体表演“技术感”。

### Hierarchy

- **Display**（700，`clamp(2.75rem, 5.2vw, 5.5rem)`，1.08）：仅用于官网首屏主张。
- **Headline**（650，`clamp(2rem, 3.6vw, 3.75rem)`，1.15）：用于官网关键叙事段标题。
- **Title**（600，20–28px，1.3）：用于界面标题、管理台页面标题和关键状态。
- **Body**（400，16px，1.7）：正文最长 68ch；手机端保持 16px。
- **Label**（600，14px，1.4）：按钮、筛选器和短状态；不把长句做成全大写或宽字距标签。

### Named Rules

**The One Instrument Face Rule.** 一个中文字体家族贯穿官网与管理台；差异来自排版节奏，而不是相似字体的随意混搭。

## 4. Elevation

系统以色调分层和清晰边界为主，阴影只出现在真实浮层、首屏工作台和拖放上传反馈中。普通内容容器保持平面，避免边框加大面积柔和阴影的“幽灵卡片”。

### Shadow Vocabulary

- **工作台悬浮**（`0 24px 64px rgba(0, 0, 0, 0.28)`）：只用于官网首屏真实软件工作台，在深色背景上形成设备感。
- **操作浮层**（`0 8px 24px rgba(18, 42, 66, 0.12)`）：只用于菜单、确认浮层和拖放中的文件对象。
- **焦点轮廓**（`0 0 0 3px rgba(30, 136, 229, 0.24)`）：键盘焦点的辅助光圈，必须同时保留清晰实线轮廓。

### Named Rules

**The Flat-by-Default Rule.** 表面静止时保持平面；阴影只说明空间或交互状态，不用于“看起来高级”。

## 5. Components

### Buttons

- **Shape:** 稳定的轻圆角（8px），最小高度 44px。
- **Primary:** 深压反馈蓝底、白字、14px 600 字重，桌面内边距 14px 22px；#1E88E5 保留为品牌识别色。
- **Hover / Focus:** 悬停变为动作悬停蓝；焦点显示 2px 实线品牌蓝轮廓和 3px 半透明辅助光圈。
- **Secondary / Ghost:** 白底深墨蓝字，使用单一结构冷线；深色首屏上的次按钮使用浅色文字与半透明白边，不使用玻璃背景。

### Chips

- **Style:** 只用于“已实现 / 研究中 / 待验证”、扫描状态和角色。小圆角 6px，不使用全胶囊作为通用标签。
- **State:** 图标或文字必须与颜色同时表达状态，避免红绿颜色成为唯一信息。

### Cards / Containers

- **Corner Style:** 功能面板 12px，产品截图外框 16px；不超过 16px。
- **Background:** 管理台使用检查台白，官网内容区可使用临床冷灰分段。
- **Shadow Strategy:** 默认无阴影，用间距和色调分层；需要浮层时引用 Elevation。
- **Border:** 表格、输入和真实分组使用结构冷线；营销段落不用每段包卡片。
- **Internal Padding:** 16、24 或 32px，遵循 8px 节奏。

### Inputs / Fields

- **Style:** 白色背景、1px 结构冷线、8px 圆角、最小 44px 高度，始终有可见标签。
- **Focus:** 2px 品牌蓝轮廓，不以颜色变浅代替焦点。
- **Error / Disabled:** 错误在字段下说明原因和修复方式；禁用同时设置语义属性、降低对比并禁止指针。

### Navigation

- 官网桌面导航透明地落在深色首屏上，滚动后变为实色；手机使用清晰的菜单按钮和整页导航，不依赖悬停。
- 管理台使用 240px 浅色侧栏和 56px 顶栏；当前项以蓝色文字、浅蓝底和短矩形标记识别，不使用彩色侧条卡片。

### Workbench Frame

真实软件截图置于 16px 圆角的深色设备框内，保留原始 UI 比例与可读标签。允许增加浏览器/桌面窗口顶栏，但不得重绘或篡改医学影像结果。合成数据必须在截图邻近位置显示“合成演示数据”标签。

## 6. Do's and Don'ts

### Do:

- **Do** 使用真实 LungTic 软件界面、项目内合成数据和明确的能力状态作为核心证据。
- **Do** 保持官网深蓝首屏与明亮内容区的“两间房”结构，管理台始终以浅色高可读为主。
- **Do** 使用 `#1E88E5` 标识焦点和当前状态，主按钮使用 `#1565C0`，并逐项校验 WCAG AA 对比度。
- **Do** 为上传、校验、扫描、发布、回滚和失败设计完整的文字状态与恢复路径。
- **Do** 在 375、390、768、1024、1440 与宽屏测试排版，不允许横向溢出。

### Don't:

- **Don't** 复制 DeepSeek Harness 的品牌、版式、文案或视觉资产。
- **Don't** 使用泛化 AI SaaS 首页、紫色霓虹、渐变文字、装饰网格、玻璃卡片堆叠、虚假大数字和相同卡片阵列。
- **Don't** 把生成式 CT 图像或未验证结果冒充产品输出。
- **Don't** 展示模型参数、训练超参数、服务器配置、默认账号、密钥或未经验证的性能与临床效果。
- **Don't** 在管理台使用营销动效、展示字体或自由拖拽页面搭建器。
- **Don't** 在普通卡片上同时使用 1px 边框和 16px 以上模糊阴影，也不要给卡片、输入或分区使用 32px 以上圆角。
