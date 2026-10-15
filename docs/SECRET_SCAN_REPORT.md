# Public Portfolio 秘密扫描报告

日期：2026-10-14。扫描对象为完整 Public Portfolio 文件树，而非仅展示媒体或部分目录。

- 工具：Gitleaks 8.24.3，默认规则，无自定义白名单，忽略代码中的 gitleaks:allow 豁免，匹配值 100% 脱敏。
- 结果：**31 条告警，核查后未发现真实秘密**。告警均为保留的上游测试样例、负向 CSRF 示例或普通文档文字；没有删除测试或改写样例来制造零告警。
- 另外逐字比对本机已知模型/环境秘密、数据库密码及非示例个人账号标识：公开文件中零匹配。acceptance 脚本中的 example.org 保留域合成账号地址会与本地测试账号同名，已核实为公开测试 fixture，不是真实个人数据；随机生成的实际密码未匹配。真实值未写入公开报告。
- 检查未携带旧开发仓库 Git 历史、真实 `.env`、账号文件、raw/private trace、数据库、已安装依赖或本地缓存。保留无秘密 `.env.example`。
- 仓库已公开；线上为无后端的 GitHub Pages 浏览器 Demo。未来新增文件后应重新扫描；模式扫描不能保证所有未知秘密均被发现。

## 复跑命令

```sh
mkdir -p tmp
gitleaks dir . --redact --ignore-gitleaks-allow --report-format json --report-path tmp/secret-scan.json
python scripts/portfolio_verify.py
```

Gitleaks 发现下列样例时会返回告警退出码，必须核查，不能将所有 tests 目录整体忽略。不要将原始私有运行记录复制到公开仓库。最终精确文件数与 SHA-256 见根目录 `PUBLIC_RELEASE_INVENTORY.json`；清单不对自身做循环哈希。

## 告警核查（不显示匹配值）

| 文件与行 | 规则 | 核查 |
|---|---|---|
| `agent-platform/backend/docs/AUTH_TEST_PLAN.md:353` | curl-auth-header | 错误 CSRF token 的负向验证示例 |
| `agent-platform/backend/docs/AUTH_TEST_PLAN.md:1680` | curl-auth-header | 错误 CSRF token 的负向验证示例 |
| `agent-platform/backend/tests/test_compose_credentials_key.py:31` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_compose_credentials_key.py:32` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_mcp_task_service.py:2972` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_notification_text.py:225` | private-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_pat_auth.py:32` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_pii_redaction_middleware.py:902` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_setup_agent_e2e_user_isolation.py:299` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skill_package_paths.py:112` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_secret_assignment_formats.py:17` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skills_installer.py:716` | private-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skills_custom_router.py:422` | private-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1581` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1604` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1615` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1627` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1638` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1645` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1693` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1843` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1843` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1914` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:1924` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_skillscan_native.py:52` | private-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_support_bundle.py:215` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_support_bundle.py:322` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_support_bundle.py:518` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_support_bundle.py:519` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/backend/tests/test_update_agent_e2e_user_isolation.py:170` | generic-api-key | 上游安全测试中的合成 fixture |
| `agent-platform/docs/superpowers/plans/2026-06-12-telegram-streaming.md:23` | generic-api-key | 普通文档文字被规则误判，无凭据赋值 |

## 完整文件树复扫

2026-10-14 对完整公开文件树 重新执行同一命令：仍为 31 条上述已核查上游 fixture/文档告警，无新增告警。旧 Git 历史未复制。精简规则不屏蔽 tests/skills/harness，真实业务代码未变。

## 静态展示发布检查

2026-10-14：展示文案、截图及报告更新后重新扫描完整仓库文件树。仍为同一组 31 条已核查样例告警，无新增告警；本机已知秘密逐字比对零匹配。此前介绍页产物不含运行配置或凭据。浏览器 Demo 新增 ES modules、合成输入与脱敏调用记录；仍无模型密钥、数据库或在线后端。

## 展示层发布复扫（2026-10-15）

完整公开文件树复扫仍为原有 31 条已核查告警，无新增。Pages 运行产物中的特定银行名称、Final Release、RED TEAM、求职等禁用文本均为零命中；内部合成客户 ID 保留，界面使用统一显示名称。
