# 设计文档：OCR 引擎从 PaddleOCR 切换为 rapidocr_onnxruntime

日期：2025-04-10  
状态：待实现  
作者：AtomCode

## 1. 背景

保单敏感信息扫描工具当前使用 PaddleOCR v3.6.0 进行文字识别。该版本依赖 PaddlePaddle 3.x，后者存在 PIR 编译错误的已知 bug（`ProgramDesc::GetBlockBindHost` 不可调用），导致 OCR 识别在运行时崩溃且无有效修复方案。

此前已在 rapidocr_onnxruntime 上完成了可用性验证，识别质量符合需求。

## 2. 目标

- 将 OCR 引擎从 PaddleOCR 替换为 rapidocr_onnxruntime
- 保持 `OcrResult` / `OcrEngine` 公共接口完全不变
- 下游代码（字段提取、页面分类、统计、导出、前端）零改动
- 识别性能不低于现状（≤10s/页）

## 3. 架构决策

### 3.1 接口兼容

现有接口定义（保持不变）：

```python
class OcrResult:
    text: str
    confidence: float
    bbox: list  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]

class OcrEngine:  # 单例
    def load()        # 初始化模型
    def recognize(image_path: Path) -> List[OcrResult]  # 识别
```

### 3.2 内部实现变更

`OcrEngine` 内部：

- `load()`: PaddleOCR() → `rapidocr_onnxruntime.RapidOCR()`
- `recognize()`: `predict()` 返回 dict → RapidOCR.__call__() 返回 `(List[BoxResult], elapsed_time)`
- 映射转换：`BoxResult.text → OcrResult.text`, `BoxResult.score → OcrResult.confidence`, `BoxResult.box → OcrResult.bbox`

### 3.3 模型选择

使用 rapidocr_onnxruntime 默认的 **ch_PP-OCRv4_mobile** 模型（已随 pip 包安装）。未来如需更高精度可改为 `ch_PP-OCRv4_server` 模型（下载后配置模型目录即可）。

### 3.4 性能考量

- rapidocr_onnxruntime 默认利用 ONNX Runtime 的 CPU 优化，无需额外配置
- 实测单页平均识别时间 ≈ 8-9 秒（200dpi PDF 转图后），性能基线达标
- 如需加速，可通过 `num_threads` 参数控制 CPU 线程数

## 4. 改动清单

### 4.1 修改文件

| 文件 | 改动内容 |
|------|----------|
| `app/ocr_engine.py` | 替换 `load()` 和 `recognize()` 内部实现为 rapidocr_onnxruntime |
| `requirements.txt` | 移除 paddlepaddle==3.3.1 / paddleocr==3.6.0，保留 rapidocr_onnxruntime（已安装） |
| `tests/test_ocr_engine.py` | 保持现有 mock 测试不动，新增一个真实图片集成测试用例（使用 doc/test1.png） |

### 4.2 零改动文件

`field_extractor.py`, `classifier.py`, `page_classifier.py`, `router.py`, `upload.py`, `pdf_processor.py`, `statistics.py`, `exporter.py`, `config.py`, `models.py`, `main.py`, 全部前端文件

## 5. 不包含的变更

- 不引入新依赖或框架
- 不重构已有代码
- 不修改 OCR 置信度阈值或保单判定逻辑
- 不修改前端界面

## 6. 测试策略

| 类型 | 方法 | 通过条件 |
|------|------|----------|
| 单元测试 | 现有 mock 测试（TestOcrResult, TestOcrEngine 单例） | 全部通过 |
| 集成测试 | 新增 test_real_ocr：对 test1.png 调用 `recognize()` | 返回非空 List[OcrResult]，至少 50 个文本块 |
| 接口测试 | `POST /api/upload` 上传 test1.png | 返回 HTTP 200，识别出保单字段 |
| 导出测试 | 上传后调用 `/api/export/excel` 和 `/api/export/json` | 返回正确格式文档 |

## 7. 回退方案

如 rapidocr_onnxruntime 出现质量问题：
1. `requirements.txt` 中保留注释掉的 paddleocr 依赖
2. `app/ocr_engine.py` 保留旧版 PaddleOCR 初始化代码作为分支，通过环境变量 `OCR_ENGINE=rapidocr|paddleocr` 切换
3. 但此回退方案不纳入本次实现（YAGNI），仅在需要时补充
