# Evidence Sources Guide

Use this checklist to collect repository evidence before drafting thesis chapters.

## Priority Sources (Read First)
1. `README*` and onboarding docs
- 项目目标、运行方式、核心能力、约束条件。
2. `docs/` design and requirement documents
- 需求范围、架构决策、演进记录、风险说明。
3. Framework configuration files
- 例如 Django `settings.py` / routing files / env templates。
4. Core domain code
- 业务模型、服务层、接口层、关键算法与调度逻辑。
5. Test artifacts
- 单元测试、集成测试、评测脚本、结果报表。
6. Deployment/operations artifacts
- 启动脚本、容器配置、CI/CD、生产检查项。

## Evidence Quality Levels
1. A级：可复现且可定位（代码+行号/函数名+测试或输出结果）。
2. B级：可定位但暂不可复现（代码或文档完整，缺运行证据）。
3. C级：仅文档声明（无代码或测试支撑，需标记“待补证据”）。

## Citation Format
Use `结论 + 证据` format:

- 结论：系统支持异步任务并行解析。
- 证据：`app/services/parser.py:142` (`ThreadPoolExecutor`), `tests/test_parser.py:55`.

## Red Flags (Do Not Claim Directly)
1. “生产可用”但没有上线检查证据。
2. “效果显著提升”但无对照实验或指标定义。
3. “高并发稳定”但无压测或监控数据。
4. “安全合规”但无审计、权限、日志策略证据。

## Minimal Evidence Table Columns
1. 结论
2. 证据路径
3. 关键行号/片段
4. 证据等级（A/B/C）
5. 备注（已实现/规划中/待补证据）
