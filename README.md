# Math-Kangaroo-Archive

袋鼠数学（Math Kangaroo / Kangourou / Känguru）资料研究档案。

本仓库保存**可复现的资料目录、来源 URL、校验值、覆盖统计、下载/更新脚本与全文索引工具**；不把第三方拥有版权的完整试卷 PDF/网页镜像直接提交到 GitHub。原始资料仅保存在用户自己的本地资料库中。

## 当前本地资料库

本地根目录默认示例：

```text
/mnt/disk1/master_data/Education/Math_Kangaroo_Library
```

在 2026-09-16 的已验证快照中，资料库包含 **1,291 个文件 / 603,150,666 字节（约 575.2 MiB）/ 847 个 PDF / 427 个 HTML**，覆盖美国、加拿大、法国、德国、奥地利和中文公开资料源；全部 1,291 个文件均已进入 SQLite FTS5 全文索引。另有 **1,584 条结构化公开样题记录**保存在本地索引中，但 GitHub 仅提交统计，不提交题目正文。精确统计见 [`data/library_summary.json`](data/library_summary.json) 与 [`data/source_coverage.csv`](data/source_coverage.csv)。

## 仓库原则

- 优先官方赛事网站、大学托管档案和明确公开的资料页。
- 不绕过登录、付费墙、访问控制或 DRM。
- 原始文件保留来源 URL、SHA256 与本地相对路径。
- GitHub 只保存元数据、代码与统计，不作为受版权材料的镜像站。
- 上游失效链接单独记录，避免把“404”伪装成已归档。

## 快速使用

```bash
python scripts/sync_official_sources.py --root /path/to/Math_Kangaroo_Library
python scripts/rebuild_index.py --root /path/to/Math_Kangaroo_Library
python scripts/search_library.py --root /path/to/Math_Kangaroo_Library --query geometry
python scripts/verify_integrity.py --root /path/to/Math_Kangaroo_Library
```

## 目录

- `data/`：不含题目正文的元数据、覆盖统计、失败链接与校验清单。
- `docs/`：来源说明、架构、数据模型与版权边界。
- `scripts/`：抓取公开官方资料、重建索引、搜索、校验、导出 GitHub 元数据。
- `.github/workflows/`：对仓库内元数据和 Python 脚本做基础验证。

## 说明

“Math Kangaroo”“Känguru der Mathematik”“Kangourou des Mathématiques”等名称与题目版权归其各自组织/权利人所有。本仓库与这些组织无隶属关系。
