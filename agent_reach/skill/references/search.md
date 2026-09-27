# 搜索工具

Agent Reach 的搜索层包含 Exa、Hacker News、ArXiv 和 Google Images。

## Exa 全网搜索

有个人 API Key 时可直接走 REST；没有 Key 时保留 mcporter/MCP 路径。

```bash
# 个人 Key 已配置时
agent-reach-exa search "query" --num-results 5

# 零配置 MCP 路径
mcporter call exa.web_search_exa query="query" numResults=5
```

需要抓正文时：

```bash
agent-reach-exa contents "https://example.com/page"
mcporter call exa.web_fetch_exa urls='["https://example.com/page"]'
```

> Exa MCP 的 `get_code_context_exa` 已弃用且默认不注册。代码问题继续用
> `web_search_exa`；精确仓库内容改用 `dev.md` 里的 GitHub 搜索。

## Hacker News

零配置。适合开发者讨论、早期项目、技术争议和创业信息。

```bash
curl -s "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=5"
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=QUERY&tags=story&hitsPerPage=5"
```

Agent Reach 内部可使用 `HackerNewsChannel.search()`、`get_item()`、
`get_stories()` 和 `get_user()`。社区讨论只能作为 community evidence；
不要自动当成 primary source。

## ArXiv

零配置，走公开 Atom API。适合论文、方法、benchmark 和学术原始来源。

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:transformer&start=0&max_results=5"
```

支持字段语法，例如 `au:Smith`、`cat:cs.CV`。ArXiv 有限流，连续请求应留间隔。

## Google Images

只走官方 Custom Search JSON API；**不要抓取 google.com 图片结果页**。

配置：

```bash
agent-reach configure google-key
agent-reach configure google-cx
```

Research Edition 内部使用 `GoogleImagesChannel.search()`。结果图片本身是 artifact；
在把图片当成证据前，应检查 `context_url`、来源页面和 provenance。

## GitHub 搜索

仓库搜索不要把多词 query 整体包进引号，否则 `gh` 会把它当成精确短语。

```bash
gh search repos arxiv api python --sort stars --limit 10
gh search code "def transcribe_audio" --language python
```

## 选型建议

| 场景 | 首选 |
|---|---|
| 通用网页发现 | Exa |
| 技术/创业社区讨论 | Hacker News |
| 学术与方法论证据 | ArXiv |
| 实物图片、PCB、产品照片 | Google Images + context page |
| 仓库、commit、代码 | GitHub |
