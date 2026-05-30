# InsShield — 保险文档敏感信息防护盾

## 项目定位

InsShield 是一款面向保险行业的文档扫描与分析工具，专注于自动检测、识别并遮蔽（脱敏）保险保单文档中的**敏感个人信息（PII，Personally Identifiable Information）**。

### 为什么需要 InsShield？

保险业务中，保单文档包含大量客户敏感信息：身份证号、手机号、银行卡号、家庭住址等。这些文档在以下场景中需要脱敏处理：

- **理赔协同** — 多家机构联合定损时，需隐藏客户隐私
- **数据标注** — 外包团队标注保单字段前，需去除可识别身份信息
- **合规审计** — 监管检查时展示最小必要信息
- **数据发布** — 内部数据集共享或公开研究时脱敏

手工脱敏效率低、易遗漏。InsShield 通过 **OCR + 规则引擎** 自动完成检测与遮蔽，大幅提升效率与准确性。

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
