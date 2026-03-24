// Markdown 渲染工具（优化版）
// 使用缓存和防抖优化性能

// 缓存已渲染的文本
const renderCache = new Map()
let lastRenderedText = ''
let lastRenderedHTML = ''

/**
 * 渲染 Markdown（带缓存优化）
 */
export function renderMarkdown(text) {
  if (!text) return ''

  // 如果文本没有变化，直接返回缓存结果
  if (text === lastRenderedText) {
    return lastRenderedHTML
  }

  // 如果是之前渲染过的文本，从缓存获取
  const cacheKey = text
  if (renderCache.has(cacheKey)) {
    lastRenderedText = text
    lastRenderedHTML = renderCache.get(cacheKey)
    return lastRenderedHTML
  }

  // 转义HTML（只在必要时处理）
  let html = text

  // 安全处理：转义特殊字符
  html = html.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 代码块 ```code```
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    // 不转义代码块内的内容
    return `<pre><code class="language-${lang || 'text'}">${code}</code></pre>`
  })

  // 行内代码 `code`
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // 粗体 **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // 斜体 *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')

  // 无序列表
  html = html.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // 有序列表
  html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>')

  // 换行
  html = html.replace(/\n/g, '<br>')

  // 缓存结果（限制缓存大小）
  if (renderCache.size > 50) {
    const firstKey = renderCache.keys().next().value
    renderCache.delete(firstKey)
  }

  renderCache.set(cacheKey, html)
  lastRenderedText = text
  lastRenderedHTML = html

  return html
}

/**
 * 清除缓存
 */
export function clearMarkdownCache() {
  renderCache.clear()
  lastRenderedText = ''
  lastRenderedHTML = ''
}

/**
 * 获取缓存统计
 */
export function getCacheStats() {
  return {
    size: renderCache.size,
    lastRenderedLength: lastRenderedText.length
  }
}
