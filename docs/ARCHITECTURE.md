# Archive Architecture

本项目分为两层：

1. **Local corpus**：原始 PDF/HTML、网页快照、全文 SQLite FTS5 索引。该层不上传 GitHub。
2. **GitHub archive**：来源清单、相对路径、SHA256、统计、失败记录、抓取和索引脚本。

推荐本地结构：

```text
Math_Kangaroo_Library/
  01_Official_USA/
  02_Canada_University_Archive/
  03_China_Public_Resources/
  04_France_Official_Archive/
  05_Germany_Official_Archive/
  06_Austria_Official_Archive/
  90_Source_Indexes/
  99_Metadata/
```

`99_Metadata/library.sqlite` 使用 SQLite FTS5，可对 PDF 提取文本、HTML 页面和结构化公开样题进行全文搜索。
