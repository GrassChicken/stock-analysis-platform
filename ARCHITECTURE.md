# 智能股票深度分析平台 — 架构设计文档

> 版本: v2.0 | 创建日期: 2026-07-23 | 更新日期: 2026-07-23
> 目标端口: **5005** | Python: **3.11** | 后端: **Flask**
> 定位: 个股深度分析工具（简洁、优美、好维护）

---

## 一、项目定位与设计原则

| 对比维度 | 智能选股平台 (5100) | 智能深度分析平台 (5005) |
|----------|---------------------|------------------------|
| 核心功能 | 全量筛选 + 评分排名 | 个股全方位深度体检 |
| 前端架构 | Vue 3 全家桶 (复杂) | Flask + Jinja2 模板 (简洁) |
| 用户场景 | 从 5000 只里选出好股票 | 对指定股票看明白 |
| UI 风格 | Element Plus (中规中矩) | Tailwind CSS (现代美观) |

### 设计原则

1. **简洁优先** — 不用 Vue/React 全家桶，Flask 模板直出页面，开发部署都简单
2. **UI 要好看** — Tailwind CSS 打造现代 UI，告别选股平台的"朴素风"
3. **按需加载** — ECharts 图表用 CDN 按需引入，不构建不打包
4. **渐进增强** — HTMX 实现轻量交互（搜索、Tab 切换、局部刷新），无需写大量 JS
5. **易于维护** — 纯 Python 项目，不依赖 Node.js，一个人就能维护

---

## 二、技术栈

| 层级 | 方案 | 版本 | 说明 |
|------|------|------|------|
| **语言** | Python | 3.11 | 稳定高效 |
| **后端框架** | Flask | 3.x | 轻量简洁，模板直出 |
| **模板引擎** | Jinja2 | 3.x | Flask 内置，组件化模板 |
| **数据源(主)** | pytdx (通达信) | 最新 | 行情/K线/财务/板块，不限流 |
| **数据源(辅)** | AKShare | 1.x | 资金流向/北向/融资融券 |
| **CSS 框架** | Tailwind CSS | 3.x | 原子化 CSS，现代美观 UI |
| **交互增强** | HTMX | 1.9+ | 轻量 AJAX，无需写 JS |
| **图表库** | Apache ECharts | 5.5+ | K线/雷达/热力图 (CDN) |
| **数据库** | SQLite | 3.x | 轻量存储分析历史/自选股 |
| **缓存** | Flask-Caching | — | 内存缓存 (小规模够用) |
| **AI 引擎** | OpenAI 兼容 API | — | 通义千问/DeepSeek |
| **部署** | Gunicorn + Nginx | — | 生产级部署 |

### 为什么不选 Vue/React？

| 考虑 | 结论 |
|------|------|
| 前端架构复杂度 | Vue 全家桶需要 Node.js + Vite + 构建流程，Flask 模板零构建 |
| UI 美观度 | Tailwind CSS 自由度高，比 Element Plus 更容易出"设计感" |
| 交互体验 | HTMX 实现 Tab 切换/搜索/局部刷新，体验接近 SPA |
| 维护成本 | 纯 Python 项目，不需要前端工程师，一个人全栈维护 |
| 部署复杂度 | 不需要 `npm build`，Flask 直接服务模板 + 静态文件 |
| 适用场景 | 深度分析是"单页数据展示"，不是"多页面应用"，模板完全够用 |

---

## 三、数据源分层架构

```
┌──────────────────────────────────────────────────┐
│                  数据源分层架构                      │
├──────────────────────────────────────────────────┤
│                                                   │
│  第一层: pytdx (通达信) ← 主力，不限流              │
│  ├── 实时行情 (get_security_quotes)                │
│  ├── K线数据 (日/周/月/分钟级)                      │
│  ├── 财务数据 (get_finance_info)                    │
│  ├── 除权除息 (get_xdxr_data)                      │
│  ├── 公司信息 (get_company_info)                    │
│  ├── 板块信息 (get_and_parse_block_file)            │
│  ├── 分笔成交 (get_transaction_data)               │
│  └── 股票列表 (get_security_list)                  │
│                                                   │
│  第二层: AKShare ← 补充 pytdx 缺失数据              │
│  ├── 资金流向 (主力/北向/南向)                       │
│  ├── 融资融券数据                                   │
│  ├── 龙虎榜数据                                    │
│  └── 行业板块涨跌                                  │
│                                                   │
│  第三层: 本地计算 ← 技术分析和指标                    │
│  ├── 技术指标: MA/MACD/KDJ/RSI/BOLL               │
│  ├── 估值分位: PE/PB/PS 历史百分位                  │
│  └── K线形态识别                                   │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 四、功能模块详细设计

### 模块总览

```
┌──────────────────────────────────────────────────────────┐
│                 智能股票深度分析平台                         │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  F1      │  F2      │  F3      │  F4      │  F5          │
│  股票搜索 │  深度分析  │  AI 解读  │  对比PK  │  分析报告     │
│  & 自选   │  仪表盘   │  报告    │  工具    │  导出         │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│  F6      │  F7      │  F8      │  F9      │  F10         │
│  基本面   │  技术面   │  资金面   │  估值面   │  行业面       │
│  分析     │  分析     │  分析     │  分析     │  分析         │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
```

---

### F1: 股票搜索 & 自选管理

**功能说明:**
- 输入股票代码/名称/拼音首字母，实时搜索匹配（HTMX 驱动）
- 搜索结果下拉展示: 代码、名称、现价、涨跌幅
- 一键加入自选股列表
- 自选股分组管理（重点关注/长线持有/短线观察）
- 自选股快速切换分析

**数据来源:** pytdx `get_security_list` + 本地搜索索引

---

### F2: 深度分析仪表盘 (核心页面)

**整体布局:**
```
┌──────────────────────────────────────────────────────┐
│ [股票名称/代码]  现价 ¥XX.XX  涨跌幅 +X.XX%         │
│ [所属行业] [所属概念板块] [市值] [PE/PB]              │
├────────────────┬─────────────────────────────────────┤
│                │                                      │
│  综合评分卡片   │       K线图 (ECharts)                │
│  ┌──────────┐  │  ┌─────────────────────────────┐    │
│  │ 总分: 85 │  │  │  日K / 周K / 月K 切换        │    │
│  │ 评级: A  │  │  │  MA/MACD/KDJ/BOLL 指标叠加   │    │
│  │ 趋势: ↑  │  │  │  成交量柱状图                 │    │
│  └──────────┘  │  │  买卖点标注                   │    │
│                │  └─────────────────────────────┘    │
│  五维雷达图     │                                      │
│  (基本面/技术面 │                                      │
│   资金面/估值面 │                                      │
│   行业面)      │                                      │
│                │                                      │
├────────────────┴─────────────────────────────────────┤
│  Tab 切换:                                            │
│  [基本面] [技术面] [资金面] [估值面] [行业面] [股东面]   │
├──────────────────────────────────────────────────────┤
│  (对应 Tab 内容区域 — HTMX 局部加载)                    │
└──────────────────────────────────────────────────────┘
```

---

### F3: 基本面深度分析

| 分析维度 | 具体指标 | 数据来源 |
|----------|----------|----------|
| **盈利能力** | ROE/ROA/毛利率/净利率/ROIC | pytdx 财务数据 |
| **成长性** | 营收增速/净利增速/连续增长季度数 | pytdx 财务数据 |
| **偿债能力** | 资产负债率/流动比率/速动比率 | pytdx 财务数据 |
| **运营效率** | 应收账款周转/存货周转/总资产周转 | pytdx 财务数据 |
| **现金流** | 经营现金流/自由现金流/现金流覆盖率 | pytdx 财务数据 |
| **杜邦分析** | ROE分解 = 净利率 × 周转率 × 杠杆倍数 | 计算得出 |

**可视化:**
- 财务指标趋势图 (近 8 个季度)
- 杜邦分析分解树状图
- 关键指标同比/环比表格
- 与行业均值对比柱状图

**AI 解读示例:**
> "该公司 ROE 连续 6 个季度保持在 20% 以上，杜邦分析显示主要由高净利率驱动（23.5%），属于典型的'护城河'型企业..."

---

### F4: 技术面深度分析

| 分析维度 | 具体指标 | 说明 |
|----------|----------|------|
| **趋势判断** | MA5/10/20/60/120/250 | 多头/空头排列判断 |
| **动量指标** | MACD/KDJ/RSI/CCI | 金叉死叉 + 顶底背离检测 |
| **波动分析** | 布林带/ATR/波动率 | 当前波动位置 |
| **量价关系** | 量比/OBV/换手率趋势 | 放量缩量分析 |
| **形态识别** | 头肩顶底/双顶底/锤子线/十字星 | K线形态自动识别 |
| **支撑阻力** | 关键价位/筹码分布 | 自动标注支撑位和压力位 |
| **买卖信号** | 综合评分/建议买卖点 | 多指标共振信号 |

**可视化:**
- 多周期 K 线图 (日/周/月/分钟级)
- 技术指标叠加层
- 支撑阻力价位图
- 技术指标仪表盘

---

### F5: 估值面分析

| 分析维度 | 具体指标 | 说明 |
|----------|----------|------|
| **绝对估值** | PE/PB/PS/PEG | 当前值 + 历史分位 |
| **历史分位** | PE/PB 近 5 年百分位 | 当前贵不贵 |
| **同行对比** | 与同行业 10 家公司对比 | 横向比较 |
| **DCF 估值** | 简化现金流折现模型 | 合理估值区间 |
| **股息率** | 当前股息率 + 历史分红 | 安全边际参考 |

**可视化:**
- PE/PB 历史走势图 + 当前分位标注
- 同行 PE 对比柱状图
- 估值仪表盘 (低估/合理/高估区间)

---

### F6: 资金面分析

| 分析维度 | 具体指标 | 数据来源 |
|----------|----------|----------|
| **主力资金** | 主力净流入/流出 (日/周/月) | AKShare |
| **北向资金** | 沪股通/深股通持股变化 | AKShare |
| **融资融券** | 融资余额变化趋势 | AKShare |
| **大单分析** | 超大单/大单/中单/小单分布 | AKShare |
| **筹码分布** | 获利盘比例/套牢盘分布 | 计算 + pytdx |
| **龙虎榜** | 机构/游资买卖情况 | AKShare |

**可视化:**
- 资金流向趋势图
- 北向资金持股变化折线
- 筹码分布图

---

### F7: 行业面分析

| 分析维度 | 具体指标 | 数据来源 |
|----------|----------|----------|
| **所属行业** | 申万一级/二级行业分类 | pytdx 板块信息 |
| **行业排名** | 行业内营收/利润/市值排名 | 计算 |
| **行业景气度** | 行业整体营收增速/PE分位 | AKShare |
| **概念题材** | 所属概念板块 (AI/新能源等) | pytdx 板块 |
| **产业链位置** | 上中下游定位 | 公司信息 + AI |

---

### F8: AI 综合分析报告

**报告结构:**
```
1. 📋 一句话总结 (20字内)
2. 🎯 综合评级 (强烈推荐/推荐/观望/回避)
3. 💪 核心优势 (3-5点)
4. ⚠️ 风险提示 (3-5点)
5. 📊 关键数据速览
6. 🔮 未来走势研判
7. 💡 操作建议 (短期/中期/长期)
```

**AI 调用策略:**
- 模型: OpenAI 兼容 API (通义千问/DeepSeek)
- 缓存: 同一股票同一天不重复调用
- 成本: 约 ¥0.02~0.05/次

---

### F9: 对比 PK 工具

- 选择 2-4 只股票横向对比
- 对比维度: 基本面/估值面/技术面/资金面
- 雷达图对比 + 数据表格
- AI 点评哪只更值得买入

---

### F10: 分析报告导出

- 生成个股深度分析 PDF 报告
- 支持自定义报告模板
- 可选: 定时自动生成自选股周报

---

## 五、项目目录结构

```
stock-analysis-platform/
│
├── app/                              # Flask 应用主目录
│   ├── __init__.py                  # Flask app 工厂函数
│   ├── config.py                    # 配置管理 (端口/数据库/AI等)
│   ├── extensions.py                # Flask 扩展初始化 (db/cache)
│   │
│   ├── routes/                      # 路由层 (URL → 视图)
│   │   ├── __init__.py
│   │   ├── main.py                 # 首页/搜索/自选股页面
│   │   ├── analysis.py             # 深度分析页面 (核心)
│   │   ├── api.py                  # JSON API (供 HTMX/图表调用)
│   │   ├── compare.py              # 对比 PK 页面
│   │   └── export.py               # 报告导出
│   │
│   ├── services/                    # 业务逻辑层 (核心!)
│   │   ├── __init__.py
│   │   │
│   │   ├── data/                    # 数据获取服务
│   │   │   ├── __init__.py
│   │   │   ├── tdx_client.py       # 通达信 pytdx 封装
│   │   │   ├── tdx_pool.py         # 连接池管理
│   │   │   ├── akshare_client.py   # AKShare 补充数据
│   │   │   └── stock_search.py     # 股票搜索索引
│   │   │
│   │   ├── analysis/                # 分析引擎
│   │   │   ├── __init__.py
│   │   │   ├── fundamental.py      # 基本面分析
│   │   │   ├── technical.py        # 技术面分析
│   │   │   │   ├── indicators.py   #   技术指标 (MA/MACD/KDJ/RSI/BOLL)
│   │   │   │   ├── patterns.py     #   K线形态识别
│   │   │   │   └── signals.py      #   买卖信号生成
│   │   │   ├── valuation.py        # 估值面分析
│   │   │   ├── capital.py          # 资金面分析
│   │   │   ├── industry.py         # 行业面分析
│   │   │   ├── scorer.py           # 综合评分引擎
│   │   │   └── ai_analyzer.py      # AI 分析引擎
│   │   │
│   │   └── utils/                   # 工具函数
│   │       ├── __init__.py
│   │       ├── market.py           # 交易日历/市场工具
│   │       ├── formatter.py        # 数据格式化
│   │       └── cache.py            # 缓存工具
│   │
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py             # SQLAlchemy 初始化
│   │   ├── stock.py                # 股票基础模型
│   │   ├── watchlist.py            # 自选股模型
│   │   └── report.py               # 分析报告模型
│   │
│   ├── templates/                   # Jinja2 模板
│   │   ├── base.html               # 基础布局 (导航/页脚/公共资源)
│   │   ├── components/             # 可复用模板组件
│   │   │   ├── stock_header.html   #   股票头部信息
│   │   │   ├── score_card.html     #   综合评分卡
│   │   │   ├── radar_chart.html    #   五维雷达图
│   │   │   ├── kline_chart.html    #   K线图组件
│   │   │   ├── tab_panel.html      #   Tab 面板组件
│   │   │   ├── finance_table.html  #   财务指标表格
│   │   │   ├── signal_list.html    #   买卖信号列表
│   │   │   ├── valuation_gauge.html#   估值仪表盘
│   │   │   ├── capital_flow.html   #   资金流向图
│   │   │   ├── ai_report.html      #   AI分析报告
│   │   │   └── compare_card.html   #   对比卡片
│   │   │
│   │   ├── pages/                   # 页面模板
│   │   │   ├── index.html          #   首页 (搜索+自选)
│   │   │   ├── analysis.html       #   深度分析页 (核心)
│   │   │   ├── compare.html        #   对比PK页
│   │   │   └── report.html         #   分析报告页
│   │   │
│   │   └── partials/               # HTMX 局部加载片段
│   │       ├── search_results.html #   搜索结果
│   │       ├── fundamental_tab.html#   基本面Tab内容
│   │       ├── technical_tab.html  #   技术面Tab内容
│   │       ├── valuation_tab.html  #   估值面Tab内容
│   │       ├── capital_tab.html    #   资金面Tab内容
│   │       ├── industry_tab.html   #   行业面Tab内容
│   │       └── ai_analysis.html    #   AI分析结果
│   │
│   └── static/                      # 静态资源
│       ├── css/
│       │   ├── app.css             # 全局样式 (Tailwind 编译产物)
│       │   └── custom.css          # 自定义覆盖样式
│       ├── js/
│       │   ├── app.js              # 全局 JS
│       │   ├── charts.js           # ECharts 图表封装
│       │   ├── kline.js            # K线图专用逻辑
│       │   └── ai-stream.js        # AI 流式输出处理
│       ├── images/
│       │   └── logo.svg
│       └── vendor/                  # 第三方库 (CDN 备选本地化)
│           ├── tailwind.min.css
│           ├── htmx.min.js
│           └── echarts.min.js
│
├── instance/                        # 实例数据 (gitignore)
│   ├── stock_analysis.db           # SQLite 数据库
│   └── cache/                       # 文件缓存
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── conftest.py                 # pytest 配置
│   ├── test_data_tdx.py            # 数据层测试
│   ├── test_analysis_fundamental.py# 基本面分析测试
│   ├── test_analysis_technical.py  # 技术面分析测试
│   ├── test_routes.py              # 路由测试
│   └── test_services.py            # 服务层测试
│
├── scripts/                         # 运维脚本
│   ├── init_db.py                  # 初始化数据库
│   ├── seed_data.py                # 种子数据
│   └── build_tailwind.sh           # Tailwind CSS 构建
│
├── deploy/                          # 部署配置
│   ├── gunicorn.conf.py            # Gunicorn 配置
│   ├── stock-analysis.service      # systemd 服务文件
│   ├── nginx.conf                  # Nginx 配置
│   └── deploy.sh                   # 一键部署脚本
│
├── .env                             # 环境变量 (gitignore)
├── .env.example                     # 环境变量示例
├── .gitignore
├── requirements.txt                 # Python 依赖
├── tailwind.config.js               # Tailwind 配置
├── restart.sh                       # 重启脚本
├── ARCHITECTURE.md                  # 本文件
├── DEVELOPMENT_PLAN.md              # 开发计划
└── README.md                        # 项目说明
```

### 目录设计说明

```
app/
├── routes/     → 只做路由分发，不包含业务逻辑
├── services/   → 核心业务逻辑全部在这里
│   ├── data/       数据获取 (pytdx/akshare)
│   ├── analysis/   分析引擎 (基本面/技术面/估值/...)
│   └── utils/      工具函数
├── models/     → 数据库模型
├── templates/  → 页面模板
│   ├── base.html       基础布局
│   ├── components/     可复用组件 (图表/卡片/表格)
│   ├── pages/          完整页面
│   └── partials/       HTMX 局部加载片段
└── static/     → 静态资源 (CSS/JS/图片)
```

**分层原则:**
- **routes** → 只负责 URL 映射和参数校验，调用 services
- **services** → 所有业务逻辑，可独立测试，不依赖 Flask
- **models** → 数据库操作，被 services 调用
- **templates** → 只负责渲染，通过 Jinja2 宏实现组件化

**迭代友好性:**
- 新增分析维度 → 只需在 `services/analysis/` 加文件 + `templates/components/` 加模板
- 新增页面 → 只需在 `routes/` 加路由 + `templates/pages/` 加页面
- 数据源切换 → 只改 `services/data/` 内部实现

---

## 六、API / 路由设计

### 6.1 页面路由 (返回 HTML)

```
GET  /                            # 首页 (搜索框 + 自选股列表)
GET  /stock/<code>                # 深度分析页 (核心页面)
GET  /stock/<code>/fundamental    # 基本面 Tab (HTMX 局部加载)
GET  /stock/<code>/technical      # 技术面 Tab (HTMX 局部加载)
GET  /stock/<code>/valuation      # 估值面 Tab (HTMX 局部加载)
GET  /stock/<code>/capital        # 资金面 Tab (HTMX 局部加载)
GET  /stock/<code>/industry       # 行业面 Tab (HTMX 局部加载)
GET  /stock/<code>/ai             # AI 分析 Tab (HTMX 局部加载)
GET  /compare                     # 对比 PK 页
GET  /watchlist                   # 自选股管理页
GET  /report/<code>               # 分析报告页
```

### 6.2 数据 API (返回 JSON, 供图表/HTMX 使用)

```
GET  /api/search?q=<keyword>                # 搜索股票
GET  /api/stock/<code>/quote                # 实时行情
GET  /api/stock/<code>/kline?period=day     # K线数据
GET  /api/stock/<code>/finance              # 财务数据
GET  /api/stock/<code>/valuation            # 估值数据
GET  /api/stock/<code>/capital-flow         # 资金流向
GET  /api/stock/<code>/signals              # 买卖信号
GET  /api/stock/<code>/radar                # 雷达图数据 (五维评分)
GET  /api/stock/<code>/score                # 综合评分
```

### 6.3 自选股 API

```
GET    /api/watchlist                       # 获取自选列表
POST   /api/watchlist                       # 添加自选股
DELETE /api/watchlist/<code>                # 删除自选股
PUT    /api/watchlist/<code>/group          # 修改分组
```

### 6.4 对比 & AI

```
POST /api/compare                           # 对比分析 (JSON body: codes[])
POST /api/ai/analyze/<code>                # 触发 AI 分析 (SSE 流式返回)
GET  /api/ai/report/<code>                 # 获取缓存的 AI 报告
```

### 6.5 导出 & 系统

```
POST /api/export/pdf/<code>                # 导出 PDF 报告
GET  /api/health                           # 健康检查
```

---

## 七、UI 设计规范

### 7.1 设计风格

- **设计语言**: 现代金融科技风 (参考 Robinhood / 富途 / Tiger 的简洁风格)
- **配色方案**:
  - 主色: 深蓝渐变 (#1e3a5f → #2563eb)
  - 强调色: 金色 (#f59e0b) 用于评分/评级
  - 背景: 浅灰 (#f8fafc) + 白色卡片
  - 涨: 红色 (#ef4444) | 跌: 绿色 (#22c55e)
- **字体**: 系统字体栈 + 数字等宽 (tabular-nums)
- **卡片**: 圆角 12px + 轻阴影 (shadow-sm) + hover 微上浮
- **间距**: Tailwind 标准间距，留白充足

### 7.2 响应式断点

```
桌面 (>1280px):  宽屏双栏，图表区最大化
平板 (768-1280px): 单栏，图表自适应宽度
手机 (<768px):   单栏卡片堆叠，简化图表
```

### 7.3 核心交互

- **搜索**: 输入即搜 (HTMX hx-trigger="keyup changed delay:200ms")
- **Tab 切换**: HTMX 局部加载，无整页刷新
- **K线图**: ECharts 原生交互 (缩放/拖拽/十字光标)
- **AI报告**: SSE 流式输出 (打字机效果)
- **评分**: 数字滚动动画 (CSS counter 或 JS)

### 7.4 视觉提升 (对比选股平台)

| 选股平台 (Element Plus) | 深度分析平台 (Tailwind CSS) |
|-------------------------|---------------------------|
| 默认蓝白配色 | 深蓝渐变 + 金色点缀 |
| 密集表格布局 | 卡片式布局，留白充足 |
| 固定间距 | 灵活间距，呼吸感 |
| 标准卡片 | 圆角+阴影+hover 动效 |
| Emoji 图标 | SVG 图标 + 渐变色 |

---

## 八、部署配置 (端口 5005)

### 8.1 环境变量

```bash
# .env
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 端口
PORT=5005

# 数据库
DATABASE_URL=sqlite:///instance/stock_analysis.db

# AI 配置
AI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_API_KEY=your-api-key
AI_MODEL=qwen-plus

# pytdx 配置
TDX_SERVERS=119.147.212.81:7709,114.80.63.12:7709
```

### 8.2 启动命令

```bash
# 开发环境
flask run --port 5005 --debug

# 生产环境
gunicorn -w 2 -b 0.0.0.0:5005 "app:create_app()"
```

### 8.3 systemd 服务

```ini
[Unit]
Description=智能股票深度分析平台
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stock-analysis-platform
Environment="PATH=/opt/stock-analysis-platform/venv/bin"
ExecStart=/opt/stock-analysis-platform/venv/bin/gunicorn \
    -w 2 -b 0.0.0.0:5005 "app:create_app()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8.4 访问方式

```
开发环境: http://localhost:5005
生产环境: http://<服务器IP>:5005
```

---

## 九、与现有选股平台的关系

```
┌────────────────────────┐         ┌────────────────────────┐
│   智能选股平台 :5100     │         │  智能分析平台 :5005      │
│   Vue 3 + FastAPI       │         │  Flask + Tailwind       │
│                        │  打通后  │                        │
│  全量筛选 → Top 股票   │ ──────→ │  输入股票 → 深度分析    │
│  评分排名 → 板块热度   │  链接跳转 │  五维分析 → AI报告     │
│                        │         │                        │
└────────────────────────┘         └────────────────────────┘
```

- **短期**: 两个项目独立开发、独立部署
- **后期**: 选股平台前端加跳转链接 → 打开分析平台 `/stock/<code>` 页面
- **共享**: 可共享 pytdx 连接池配置、AI API Key

---

## 十、依赖清单

```txt
# requirements.txt

# 核心框架
Flask==3.1.*
Flask-SQLAlchemy==3.1.*
Flask-Caching==2.3.*

# 数据源
pytdx==1.72
mootdx==0.9.*        # pytdx 的增强封装
akshare==1.14.*

# 数据处理
pandas==2.2.*
numpy==1.26.*

# 技术指标计算
ta-lib==0.5.*        # 需要系统安装 TA-Lib C 库
# 或者纯 Python 备选: pandas-ta==0.3.*

# AI
openai==1.50.*       # OpenAI 兼容 API 客户端

# 工具
python-dotenv==1.0.*
requests==2.32.*
gunicorn==23.*

# PDF 导出 (可选)
weasyprint==62.*     # HTML → PDF
```

---

*文档版本: v2.0 | 创建日期: 2026-07-23 | 更新日期: 2026-07-23*
*项目: 智能股票深度分析平台 | 目标端口: 5005 | 技术栈: Python 3.11 + Flask + Tailwind CSS*
