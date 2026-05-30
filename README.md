# InsShield — 保险行业个人信息监测扫描工具

## 项目定位

InsShield 是一款面向保险行业的**个人信息监测扫描**工具。

### 核心区别：找"字段" vs 找"人"

传统敏感信息工具的工作方式是**字段匹配**——在文档中搜索与身份证号（18位数字）、手机号（11位数字）、银行卡号等正则模式匹配的字符串。它不关心这些信息属于谁，也不关心一份文档中提到的是一个人还是多个人。

InsShield 以**人为主体**：

| 维度 | 传统工具（字段中心） | InsShield（人中心） |
|------|-------------------|-------------------|
| 检测目标 | 匹配字符串模式（身份证号、手机号等） | 识别一个完整**个人信息主体**所关联的所有信息 |
| 信息组织 | 按类型分类（有多少个身份证、多少个手机号） | 按人聚合（张三关联了哪些信息，李四关联了哪些信息） |
| 关系理解 | 不关心信息之间的归属关系 | 识别哪些信息属于同一个人 |
| 多人文档 | 无法区分甲的信息和乙的信息 | 能区分不同个人信息主体的信息边界 |
| 上下文判断 | 只看局部字符模式 | 结合上下文判断信息主体身份和关系 |

### 什么是"个人信息监测扫描"？

以一份保单为例，传统工具扫描结果是：
> ✅ 找到身份证号 ×1，手机号 ×1，银行卡号 ×1

InsShield 的扫描结果是：
> ✅ 张三个人信息集合：身份证号、手机号、家庭住址、联系方式  
> ✅ 李四个人信息集合：身份证号、银行卡号  
> ⚠️ 发现一条地址信息无法确定归属，需人工确认

前者告诉你"有哪些敏感字段"，后者告诉你"有哪些人的信息、各关联了什么信息、还有哪些信息归属不明"——这是根本性的差异。

### 为什么需要 InsShield？

保险业务中，保单文档包含大量客户个人信息。这些文档在以下场景中需要处理：

- **理赔协同** — 多家机构联合定损时，涉及多个被保险人的个人信息交叉
- **数据标注** — 外包团队标注保单字段前，需明确每个标注对象的信息边界
- **合规审计** — 监管要求"最小必要"原则，传统工具只看字段数量，无法评估"每个人的信息是否最小"
- **数据发布** — 内部数据集共享或公开研究时，需确保每个个人信息主体都被脱敏

InsShield 通过 **以人为主体的信息聚合 + OCR + 规则引擎**，完成从"检测敏感字段"到"监测个人信息"的升级。

## 功能特性

- **多格式支持** — 解析 PDF 和 Word（`.docx`）文档
- **OCR 引擎** — 内置快速 OCR，支持 PDF 中的扫描图片识别（基于 RapidOCR）
- **PII 检测** — 自动识别文档中的身份证号、手机号、银行卡号、地址、姓名等敏感信息
- **文档分类** — 智能分类文档类型：身份证、保单、银行流水等
- **字段提取** — 按页面布局提取关键结构化字段
- **可视化预览** — Web 界面支持上传、预览和高亮标注敏感区域
- **数据导出** — 导出脱敏后的文档，安全共享
- **统计看板** — 文档数量、PII 类型及检测分布汇总，帮助评估脱敏覆盖率

### 为什么这样设计统计？

统计看板的核心目的是让用户**快速了解脱敏工作的整体状况**：

| 指标 | 目的 |
|---|---|
| 文档总数 / 已检测文档数 | 了解整体处理进度 |
| PII 类型分布（身份证/手机号/银行卡等） | 识别最常见的敏感数据类型，针对性优化检测规则 |
| 各文档 PII 命中数量 | 评估文档敏感程度，发现异常高敏文档 |
| 按日/周的趋势统计 | 追踪脱敏工作量的变化 |

统计不是为"好看"，而是为**决策** — 比如发现某类文档的身份证号命中率异常高，就应该优先优化这类文档的检测规则。

## 快速开始

### 环境要求

- Python 3.10+
- pip / uv

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/ins-shield.git
cd ins-shield

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 启动 Web 服务
uvicorn main:app --reload --port 8000
```

在浏览器中打开 http://localhost:8000

### 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
ins-shield/
├── main.py                  # FastAPI 入口（应用启动点）
├── requirements.txt         # Python 依赖
├── app/                     # 应用核心
│   ├── __init__.py          # 包声明
│   ├── router.py            # API 路由
│   ├── config.py            # 配置
│   ├── models.py            # Pydantic 数据模型
│   ├── upload.py            # 文件上传处理
│   ├── pdf_processor.py     # PDF 解析 + OCR 调度
│   ├── word_processor.py    # Word 文档解析
│   ├── ocr_engine.py        # OCR 识别引擎（基于 RapidOCR）
│   ├── pii_extractor.py     # PII 检测引擎（规则 + 模式匹配）
│   ├── field_extractor.py   # 结构化字段提取
│   ├── classifier.py        # 文档分类
│   ├── doc_classifier.py    # 文档类型分类器
│   ├── page_classifier.py   # 页面级别分类器
│   ├── exporter.py          # 脱敏结果导出
│   ├── statistics.py        # 统计看板数据聚合
│   └── logger.py            # 日志配置
├── static/                  # 前端资源
│   ├── index.html           # 主页面
│   ├── style.css            # 样式
│   └── script.js            # 前端逻辑
├── tests/                   # 测试套件
│   ├── test_pdf_processor.py
│   ├── test_word_processor.py
│   ├── test_pii_extractor.py
│   ├── test_field_extractor.py
│   ├── test_classifier.py
│   ├── test_doc_classifier.py
│   ├── test_page_classifier.py
│   ├── test_exporter.py
│   ├── test_statistics.py
│   ├── test_router.py
│   └── test_upload.py
├── test_images/             # 测试用文档样本（仅用于测试）
│   ├── pdf/                 # 测试用 PDF 文件
│   ├── docx/                # 测试用 Word 文件
│   ├── images/              # 测试用扫描件图片
│   └── layouts.json         # 页面布局配置数据
└── docs/                    # 文档
```

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/upload/` | 上传文档 |
| POST | `/api/scan/` | 触发 OCR + PII 扫描 |
| GET | `/api/results/{task_id}` | 获取扫描结果 |
| GET | `/api/statistics/` | 看板统计数据 |
| GET | `/api/export/{task_id}` | 导出脱敏结果 |
| POST | `/api/classify/` | 文档类型分类 |

## 技术栈

- **后端** — Python, FastAPI, RapidOCR, pdfplumber, python-docx
- **前端** — HTML, CSS, JavaScript（原生）
- **PII 引擎** — 规则匹配 + 模式识别（身份证号/手机号/银行卡号校验）

## 许可证

MIT © 2024 InsShield Contributors
