# Data Model

`data/inventory.csv` 主要字段：

- `path`: 本地资料库相对路径
- `ext`: 文件扩展名
- `size`: 字节数
- `sha256`: 内容哈希
- `year`: 推断年份
- `level`: A–F（若可识别）
- `grades`: 年级范围
- `language`: 语言标签
- `text_chars`: 本地索引提取到的文本字符数
- `source_url`: 原始公开来源 URL（若已知）

`data/sample_question_stats.csv` 仅保存结构化公开样题的统计，不提交题目全文。
