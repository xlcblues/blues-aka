// Markdown 渲染工具（完整版）
// 支持代码、公式、表格、列表等所有 Markdown 元素

// 缓存已渲染的文本
const renderCache = new Map()
let lastRenderedText = ''
let lastRenderedHTML = ''

/**
 * 渲染 Markdown（完整版，支持数学公式）
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

  let html = text

  // ========== 第一阶段：保护代码块和数学公式 ==========
  const protectedBlocks = []

  // 1. 保护数学公式（LaTeX）
  // 块级公式 $$...$$
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
    protectedBlocks.push({
      type: 'math-block',
      content: formula.trim()
    })
    return `__BLOCK_${protectedBlocks.length - 1}__`
  })

  // 行内公式 $...$
  html = html.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    protectedBlocks.push({
      type: 'math-inline',
      content: formula.trim()
    })
    return `__BLOCK_${protectedBlocks.length - 1}__`
  })

  // 2. 保护代码块 ```lang ... ```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    protectedBlocks.push({
      type: 'code-block',
      lang: lang || 'text',
      content: code
    })
    return `__BLOCK_${protectedBlocks.length - 1}__`
  })

  // ========== 第二阶段：转义 HTML ==========
  html = html.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // ========== 第三阶段：处理其他 Markdown 元素 ==========

  // 标题 # text
  html = html.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>')
  html = html.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>')
  html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')

  // 引用块 > text
  html = html.replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>')
  html = html.replace(/(<blockquote>[^<]*<\/blockquote>(\n<blockquote>[^<]*<\/blockquote>)+)/g,
    '<blockquote class="quote-block">$&</blockquote>')

  // 分隔线 ---, ___, ***
  html = html.replace(/^---$/gm, '<hr class="md-hr">')
  html = html.replace(/^\*\*\*$/gm, '<hr class="md-hr">')
  html = html.replace(/^___$/gm, '<hr class="md-hr">')

  // Markdown 表格
  html = html.replace(/^[|]?\s*([^|\n]+)\s*\|[\s\S]*?$/gm, (match) => {
    if (!match.includes('|')) return match

    const rows = match.trim().split('\n')
    if (rows.length < 2) return match

    const separatorRow = rows[1].trim()
    if (!separatorRow.match(/^[\s\|:-]+$/)) return match

    let tableHtml = '<div class="md-table-wrapper"><table class="md-table">'

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i].trim()
      if (!row) continue

      const cells = row.replace(/^\||\|$/g, '').split('|').map(cell => cell.trim())

      if (i === 0) {
        // 表头
        tableHtml += '<thead><tr>'
        cells.forEach(cell => {
          tableHtml += `<th>${cell}</th>`
        })
        tableHtml += '</tr></thead><tbody>'
      } else if (i > 1) {
        // 数据行（跳过分隔符行）
        tableHtml += '<tr>'
        cells.forEach(cell => {
          tableHtml += `<td>${cell}</td>`
        })
        tableHtml += '</tr>'
      }
    }

    tableHtml += '</tbody></table></div>'
    return tableHtml
  })

  // 行内代码 `code`
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // 粗体 **text** 和 __text__
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>')

  // 斜体 *text* 和 _text_
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>')

  // 删除线 ~~text~~
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="md-link">$1</a>')

  // 图片 ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="md-image" />')

  // 无序列表 - item, * item, + item
  html = html.replace(/^\s*[-*+]\s+(.+)$/gm, '<li class="list-item">$1</li>')

  // 有序列表 1. item
  html = html.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<li class="list-item" data-value="$1">$2</li>')

  // 合并连续列表项
  html = html.replace(/(<li class="list-item"[^>]*>.*<\/li>\n?)+/g, (match) => {
    // 检查是否是有序列表
    const hasNumbers = match.includes('data-value')
    const tag = hasNumbers ? 'ol' : 'ul'
    return `<${tag} class="md-list">${match}</${tag}>`
  })

  // ========== 第四阶段：先恢复代码块和公式块 ==========
  html = html.replace(/__BLOCK_(\d+)__/g, (match, index) => {
    const block = protectedBlocks[index]
    if (block.type === 'code-block') {
      return `<pre class="md-code-block" data-language="${block.lang}"><code class="language-${block.lang}">${block.content}</code></pre>`
    } else if (block.type === 'math-block') {
      return `<div class="math-block">${block.content}</div>`
    } else if (block.type === 'math-inline') {
      return `<span class="math-inline">${block.content}</span>`
    }
    return match  // html-block 类型保持原样，后续处理
  })

  // ========== 第五阶段：段落处理 ==========
  // 保护 HTML 块（现在只保护真正的HTML，代码块和公式已经恢复）
  html = html.replace(/<(h[1-6]|ul|ol|li|blockquote|table|div|hr|pre)[^>]*>[\s\S]*?<\/\1>/gi, (match) => {
    protectedBlocks.push({
      type: 'html-block',
      content: match
    })
    return `__BLOCK_${protectedBlocks.length - 1}__`
  })

  // 处理段落
  const lines = html.split('\n')
  const processedLines = []
  let currentParagraph = []

  for (const line of lines) {
    if (line.trim() === '' || line.startsWith('__BLOCK_')) {
      if (currentParagraph.length > 0) {
        processedLines.push(`<p class="md-paragraph">${currentParagraph.join(' ')}</p>`)
        currentParagraph = []
      }
      if (line.startsWith('__BLOCK_')) {
        processedLines.push(line)
      }
    } else {
      currentParagraph.push(line)
    }
  }

  if (currentParagraph.length > 0) {
    processedLines.push(`<p class="md-paragraph">${currentParagraph.join(' ')}</p>`)
  }

  html = processedLines.join('\n')

  // 恢复 HTML 块
  html = html.replace(/__BLOCK_(\d+)__/g, (match, index) => {
    const block = protectedBlocks[index]
    if (block.type === 'html-block') {
      return block.content
    }
    return match
  })

  // 软换行：单个换行符转为 <br>（但不在 HTML 块内）
  html = html.replace(/\n(?!<)/g, '<br>\n')

  // 清理多余的 <br>
  html = html.replace(/(<\/(?:h[1-6]|p|li|td|th|blockquote|div|ul|ol|pre)>)<br>/gi, '$1')
  html = html.replace(/<br>\s*(<<(?:h[1-6]|p|li|td|th|blockquote|div|ul|ol|pre))/gi, '$1')

  // 缓存结果
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
