# 本项目已停止维护

> **状态：已归档 / 不再维护（Read-only）**
> 声明日期：2026-11-10

本仓库（SkBookBot）自即日起**停止维护**，不再进行功能开发、版本更新、Bug 修复，也不再处理 Issue 与 Pull Request。仓库已设置为 **Archived（只读）**，全部内容保持现状，仅作存档与查阅用途。

## 这意味着什么

- 仓库已归档，无法再提交代码、创建 Issue / PR、发布 Release 或修改配置。
- 不再发布新版本；`web/` 面板内置的「版本更新检查」（`GET /api/update-check`）不会有后续更新，请直接忽略。
- 项目所依赖的 SkBook 开放平台（v1，<https://skbookv1.sk68.top>）若后续变更接口，本项目不会跟进适配。
- 代码按「现状」提供，不提供任何形式的持续支持或兼容性保证。

## 归档时的最后状态

- 已完成 SkBook API **v1 新域名**迁移（`skbookv1.sk68.top`），并封装 `get_bot_info/`、`get_dm_messages/` 两个 v1 接口及对应管理 API。
- Web 管理面板 Vue 源码已回迁至本仓库 `frontend/`，构建产物位于 `web/`（由 `core/server/http_server.py` 托管）。
- 独立面板仓库 `SKbook-Bot-Web` 已停止维护，源码不再单独使用（已并入本仓库 `frontend/`）。
- 已知未完成项见 `V1_MIGRATION.md` 第五节（私信消息自动轮询与分发、前端私信/机器人信息页接入等），**不再继续实现**。

## 如需继续使用

归档仓库仍可 `git clone` / Fork。如需继续开发，请 Fork 本仓库后自行维护，或由仓库所有者解除归档状态。后续一切维护工作均由使用者自行承担。

---

*本项目到此为止，感谢使用。*
