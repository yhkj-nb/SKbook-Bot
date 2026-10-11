# SkBookBot · API v1 迁移与补全报告

> 生成时间：2026-10-11
> 配套文档：`SkBook开放平台API文档_v1新域名.md`（用户提供，提取于 2026-10-07）

## 一、问题诊断（为什么这是个"烂项目"）

通过比对用户提供的 **v1 新域名 API 文档** 与仓库代码（最后提交 2026-09-12，比文档早一个月），确认核心问题是：

1. **API 域名已废弃，整个机器人实际已失效**
   - 代码写死旧域名 `https://skbook.sk26.cn`
   - 新域名为 `https://skbookv1.sk68.top`（旧域名已停用）
   - 任何接口调用都会打到死域名 → 机器人无法收发消息、无法鉴权

2. **v1 新增的两个接口未封装**
   - `get_bot_info/`（获取机器人自身信息与授权社区）
   - `get_dm_messages/`（获取私信消息）
   - 框架 README 声称"封装了全部接口"，但这两个 v1 接口缺失

3. **前端文档链接指向旧域名**
   - `SKbook-Bot-Web/src/views/Settings.vue` 的"API 文档"链接指向 `https://skbook.sk26.cn`

---

## 二、本次改动清单

### 后端（仓库 `SKbook-Bot`）

| 文件 | 改动 |
|------|------|
| `core/network/api_client.py` | ① `BASE_URL` 改为 `https://skbookv1.sk68.top/open/api/`<br>② `OAuth2Client.AUTH_URL` / `API_URL` 改为新域名<br>③ **新增** `get_bot_info()` 方法（v1 接口 1）<br>④ **新增** `get_dm_messages()` 方法（v1 接口 2）<br>⑤ 同步更新模块/类文档字符串 |
| `core/bot/instance.py` | ① 新增 `fetch_bot_info()`：启动时校验 TOKEN 并拉取机器人信息<br>② `start()` 中在轮询前先调用 `fetch_bot_info()`（失败不阻断轮询）<br>③ 新增属性 `bot_info` / `bot_user_id` / `default_community_id`（为私信功能预留） |
| `core/server/http_server.py` | ① 新增路由 `GET /api/bot-info` 与 `GET /api/dm-messages`<br>② 新增对应处理器（含鉴权、参数校验、错误映射）<br>③ `/api/bots` 返回字段补充 `bot_user_id` / `default_community_id` / `bot_name` |
| `README.md` | ① 平台链接与说明改为新域名<br>② API 概览表补充 `get_bot_info/` 与 `get_dm_messages/`<br>③ 增加 v1 迁移说明与文档链接 |

### 前端（仓库 `SKbook-Bot-Web`）

| 文件 | 改动 |
|------|------|
| `src/views/Settings.vue` | "API 文档"链接由 `https://skbook.sk26.cn` 改为 `https://skbookv1.sk68.top/open/docs.php` |

> 说明：前端仅作为面板与本地后端（`localhost:5200`）通信，无直接调用 SkBook API 的域名硬编码，故只需修正文档链接。

---

## 三、校验结果

- ✅ 三个改动的后端 Python 文件均通过 `python3.11 -m py_compile` 语法编译
- ✅ 全量检查：`skbook.sk26.cn/open` 已无任何实际接口 URL 误用（仅保留两处"旧域名已停用"的文档说明）
- ✅ 新域名 `skbookv1.sk68.top` 已落到 `api_client.py` / `README.md` / `Settings.vue`
- ✅ `get_bot_info` / `get_dm_messages` 方法与 `/api/bot-info` / `/api/dm-messages` 路由均已落地

---

## 四、如何应用这些改动

### 后端（补丁文件已生成在 `SKbook-Bot/` 目录，按相对路径覆盖到你的 clone）

```bash
# 假设你的 clone 在 ~/code/SKbook-Bot
cp -r /path/to/SKbook-Bot/core  ~/code/SKbook-Bot/
cp      /path/to/SKbook-Bot/README.md ~/code/SKbook-Bot/
# 覆盖后建议跑一次语法检查
cd ~/code/SKbook-Bot && python3 -m py_compile core/network/api_client.py core/bot/instance.py core/server/http_server.py
```

### 前端（已在本机仓库内直接修改 `Settings.vue`）

```bash
cd SKbook-Bot-Web
# 重新构建以更新后端内置的 web/ 产物（需 Node 18+）
npm install && npm run build   # 产物输出至 ../SKbook-Bot/web/
```

---

## 五、未覆盖的后续项（建议继续完成）

| 优先级 | 项 | 说明 |
|--------|----|------|
| 🔴 高 | **私信消息自动轮询与分发** | v1 已提供 `get_dm_messages`，但当前 `BotInstance` 仅轮询频道消息。完整私信能力需：①新增 `_poll_dm()` 轮询循环 + 游标去重；②`MessageEvent` 增加 `is_dm` 标记；③`send_dm` 需 `community_id`，可由 `default_community_id`（授权社区首个）兜底；④按 `bot_user_id` 过滤机器人自己发出的消息以防回声。本次已预留 `default_community_id` / `bot_user_id`，但未实现自动轮询。 |
| 🟡 中 | **前端面板接入私信/机器人信息页** | 新增的 `/api/bot-info`、`/api/dm-messages` 后端已就绪，但前端 `Messages.vue` / `Bots.vue` 尚未调用；可考虑在机器人管理页展示 `bot_name` / 授权社区。 |
| 🟡 中 | **更新检查接口** | `http_server._handle_update_check` 仍依赖 GitHub Releases；若后续改用 Vercel/自有分发，需同步调整。 |
| 🟢 低 | **补充单元测试** | `api_client` 的请求构造、错误码映射、卡片 JSON 组装建议补 pytest 用例。 |
| 🟢 低 | **卡片消息示例对齐文档** | `docs/plugin-development.md` 的卡片示例可补充 v1 文档中的"签到提醒""活动通知"两个完整示例。 |

---

## 六、关于提交 / 推送

本环境无法直连 GitHub（TLS 被沙箱网络策略中断），因此 **未能执行 `git push`**。
- 前端 `SKbook-Bot-Web` 已是本地真实仓库，改动已落入工作区，可在网络恢复后：
  ```bash
  git add src/views/Settings.vue && git commit -m "fix: 文档链接迁移至 SkBook API v1 新域名" && git push
  ```
- 后端改动以补丁文件形式提供（见上方目录），覆盖进 clone 后同样可一次性提交推送。

---

## 七、改动文件索引（本交付物）

- `SKbook-Bot/core/network/api_client.py` — **已替换**（v1 域名 + 两新接口）
- `SKbook-Bot/core/bot/instance.py` — **已替换**（启动校验 + 预留属性）
- `SKbook-Bot/core/server/http_server.py` — **已替换**（两新管理 API）
- `SKbook-Bot/README.md` — **已替换**（新域名 + 接口表）
- `SKbook-Bot-Web/src/views/Settings.vue` — **已原地修改**（文档链接）
