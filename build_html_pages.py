#!/usr/bin/env python3
"""把 .md 预渲染成独立 HTML 页面（米白衬线设计，与主站一致）。

跑法：
    cd "Personal show"
    python build_html_pages.py
"""
import os
import re
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DOCS = [
    ('librarian output/Geely.md',                                              'geely-wiki.html',       'Geely · Coverage Wiki — 吉利汽车 / 0175.HK',                  'Holdings Wiki · Stage 01 output'),
    ('librarian output/Chery.md',                                              'chery-wiki.html',       'Chery · Coverage Wiki — 奇瑞汽车 / 9973.HK',                  'Holdings Wiki · Stage 01 output'),
    ('librarian output/2026-05-11_analysis_GPM-drivers-QA.md',                 'gpm-drivers.html',      'Chery GPM Drivers — 五季度从 10.6% 反弹到 16.0%',             '任务级辅助 · 跨源综合 · 2026-05-11'),
    ('librarian output/2026-05-11_meeting-prep_CICC-analyst-question-list.md', 'cicc-list.html',        'CICC 分析师交流 — Question List v3',                          '会前 briefing → 会后闭环 · 2026-05-11'),
    ('2026-05-16_失败是通向成功的金矿.md',                                      'essay-failure.html',        '失败是金矿 — 可怕的是 not even wrong',                       'Essay · 2026-05-16'),
    ('2026-05-15_data-validator机制_三维正交模型_脱敏版.md',                   'essay-data-validator.html', 'data-validator 机制 — 金融数据信任的三维正交模型',          'Essay · 2026-05-15'),
    ('2026-05-13_AI-Agent三层架构_Guide-Hook-Eval_脱敏版.md',                  'essay-ghe.html',        'Guide / Hook / Eval — 三层 Skill 设计',                       'Essay · 2026-05-13'),
    ('2026-05-12_Claude-Code-Skills-Network_visual.md',                        'essay-skills-net.html', 'Claude Code Skills Network — 视觉架构图',                     'Essay · 2026-05-12'),
    ('2026-05-11_Librarian升级_从记忆系统到主动投研助手.md',                  'essay-librarian.html',  'Librarian 升级 — 从记忆系统到主动投研助手',                    'Essay · 2026-05-11'),
    ('2026-04-14_Claude_Code_投研工作站架构_v2_脱敏版.md',                    'essay-arch-v2.html',    'Claude Code 投研工作站架构 v2.0',                              'Essay · 2026-04-14'),
    ('2026-04-14_用Obsidian构建持久化的投研记忆系统.md',                      'essay-memory.html',     '用 Obsidian 构建持久化的投研记忆系统',                         'Essay · 2026-04-14'),
    ('2026-04-19__Cowork平台战略思考_个人视角_v2.md',                          'cowork-strategy.html',  'Cowork 平台战略思考 —— 被低估的中间层',                        'Essay · 2026-04-19'),
    ('2026-04-06_Cowork_to_Claude_Code_Migration_desensitized.md',            'cowork-migration.html', '从 Cowork 迁移到 Claude Code',                                'Essay · 2026-04-06'),
]


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def strip_end_period(s):
    """剥离段落末尾的句号（中文 。 或英文 .）"""
    return re.sub(r'[。.]\s*$', '', s)


def render_inline(s):
    """渲染行内元素"""
    # Obsidian wikilinks [[path|display]] / [[text]]
    s = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]',
               lambda m: f'<span class="wl" title="{esc(m.group(1))}">{m.group(2)}</span>', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'<span class="wl">\1</span>', s)
    # Inline code (escape content)
    s = re.sub(r'`([^`\n]+)`', lambda m: f'<code>{esc(m.group(1))}</code>', s)
    # Bold
    s = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'__([^_\n]+)__', r'<strong>\1</strong>', s)
    # Italic (asterisk + 安全的 underscore —— underscore 前后必须不是字母/数字/下划线，避免误匹配 file_name)
    s = re.sub(r'(^|[^*])\*([^*\n]+)\*(?!\*)', r'\1<em>\2</em>', s)
    s = re.sub(r'(?<![a-zA-Z0-9_])_([^_\n]{1,200}?)_(?![a-zA-Z0-9_])', r'<em>\1</em>', s)
    # Markdown links [text](url)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def render_markdown(md):
    """把 markdown 渲染成 HTML 字符串"""
    # 剥离 YAML frontmatter —— 兼容 --- / *** 开头，以及 --- 或 ***（任意长度） 结尾
    md = re.sub(r'^(?:---|\*\*\*)\r?\n[\s\S]*?\r?\n[-*]{3,}\r?\n+', '', md, count=1)
    # 剥离 Obsidian 块锚点 ^anchor-name（可能包含中英文字）
    md = re.sub(r' *\^[a-zA-Z][^\s\n]*', '', md)
    # 剥离整行都是 Obsidian inline tag 的行（#tag #tag ...，注意 markdown 标题是 "# " 带空格，不会误伤）
    md = re.sub(r'^#[A-Za-z][\w-]*(?:[ \t]+#[A-Za-z][\w-]*)*[ \t]*$', '', md, flags=re.MULTILINE)

    lines = md.split('\n')
    out = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            out.append(f'<pre><code>{esc(chr(10).join(code))}</code></pre>')
            continue

        # Header
        h = re.match(r'^(#{1,6})\s+(.*)$', line)
        if h:
            level = len(h.group(1))
            out.append(f'<h{level}>{render_inline(h.group(2))}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^\s*[-*_]{3,}\s*$', line):
            out.append('<hr>')
            i += 1
            continue

        # Table
        if ('|' in line and i + 1 < len(lines)
                and re.match(r'^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$', lines[i + 1])):
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip() != '':
                rows.append(lines[i])
                i += 1
            if len(rows) >= 2:
                def parse_row(r):
                    r = re.sub(r'^\s*\|', '', r)
                    r = re.sub(r'\|\s*$', '', r)
                    # 保护 [[...|...]] 内的 | 不被当成表格列分隔符
                    r = re.sub(r'\[\[[^\]]*?\]\]',
                               lambda m: m.group(0).replace('|', '\x00'), r)
                    return [c.strip().replace('\x00', '|') for c in r.split('|')]

                head = parse_row(rows[0])
                body = [parse_row(r) for r in rows[2:]]
                tbl = ['<table><thead><tr>']
                for c in head:
                    tbl.append(f'<th>{render_inline(c)}</th>')
                tbl.append('</tr></thead><tbody>')
                for r in body:
                    tbl.append('<tr>')
                    for c in r:
                        tbl.append(f'<td>{render_inline(c)}</td>')
                    tbl.append('</tr>')
                tbl.append('</tbody></table>')
                out.append(''.join(tbl))
            continue

        # Blockquote — 递归解析内容；识别 Obsidian callout [!type]
        # 兼容缩进 > （列表项内嵌的 callout / 备注引用）
        stripped = line.lstrip()
        if stripped.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].lstrip().startswith('>'):
                bq_lines.append(re.sub(r'^>\s?', '', lines[i].lstrip()))
                i += 1
            bq_content = '\n'.join(bq_lines)
            # Obsidian callout: > [!type] optional title
            callout = re.match(r'^\[!(\w+)\][+-]?\s*(.*?)$', bq_content.split('\n', 1)[0])
            if callout:
                ctype = callout.group(1).lower()
                ctitle = callout.group(2).strip()
                rest = '\n'.join(bq_content.split('\n')[1:])
                rendered = render_markdown(rest) if rest.strip() else ''
                title_html = f'<div class="callout-title">{render_inline(ctitle)}</div>' if ctitle else ''
                out.append(f'<div class="callout callout-{ctype}">{title_html}<div class="callout-body">{rendered}</div></div>')
            else:
                rendered = render_markdown(bq_content)
                out.append(f'<blockquote>{rendered}</blockquote>')
            continue

        # 收集列表项 + 处理嵌套子列表（缩进的 - / * / +）和续行
        def collect_list_item(parent_prefix_re, lines_, idx):
            """返回 (item_html, next_idx)。parent_prefix_re 已经匹配过当前行。"""
            content = re.sub(parent_prefix_re, '', lines_[idx])
            j = idx + 1
            nested_items = []
            while j < len(lines_):
                ln = lines_[j]
                # 缩进 bullet 视为子列表
                m_nested = re.match(r'^\s{2,}[-*+]\s+(.*)', ln)
                if m_nested:
                    nested_items.append(m_nested.group(1))
                    j += 1
                    # 子项续行
                    while j < len(lines_) and re.match(r'^\s{4,}\S', lines_[j]) and not re.match(r'^\s{2,}[-*+]\s', lines_[j]):
                        nested_items[-1] += ' ' + lines_[j].strip()
                        j += 1
                    continue
                # 普通缩进续行（非 bullet）
                if re.match(r'^\s{2,}\S', ln) and not re.match(r'^\s{2,}[-*+]\s', ln) and not re.match(r'^\s{2,}\d+\.\s', ln):
                    if nested_items:
                        nested_items[-1] += ' ' + ln.strip()
                    else:
                        content += ' ' + ln.strip()
                    j += 1
                    continue
                break
            html = render_inline(strip_end_period(content))
            if nested_items:
                html += '<ul>' + ''.join(f'<li>{render_inline(strip_end_period(ni))}</li>' for ni in nested_items) + '</ul>'
            return html, j

        # Unordered list
        if re.match(r'^[-*+]\s+', line):
            items_html = []
            while i < len(lines) and re.match(r'^[-*+]\s+', lines[i]):
                item_html, i = collect_list_item(r'^[-*+]\s+', lines, i)
                items_html.append(item_html)
            out.append('<ul>' + ''.join(f'<li>{h}</li>' for h in items_html) + '</ul>')
            continue

        # Ordered list
        if re.match(r'^\d+\.\s+', line):
            items_html = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                item_html, i = collect_list_item(r'^\d+\.\s+', lines, i)
                items_html.append(item_html)
            out.append('<ol>' + ''.join(f'<li>{h}</li>' for h in items_html) + '</ol>')
            continue

        # Blank line
        if line.strip() == '':
            i += 1
            continue

        # Paragraph
        para = []
        while (i < len(lines) and lines[i].strip() != ''
               and not re.match(r'^#{1,6}\s', lines[i])
               and not re.match(r'^[-*+]\s', lines[i])
               and not re.match(r'^\d+\.\s', lines[i])
               and not lines[i].startswith('>')
               and not lines[i].startswith('```')
               and not re.match(r'^\s*[-*_]{3,}\s*$', lines[i])):
            para.append(lines[i])
            i += 1
        if para:
            out.append(f'<p>{render_inline(strip_end_period(" ".join(para)))}</p>')

    # 正文首个 H1 与模板 doc-title 重复 —— 去掉
    if out and out[0].startswith('<h1>'):
        out = out[1:]

    return '\n'.join(out)


TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}} — 投研架构笔记</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #F3EEE4;
    --bg-2: #EFE8DA;
    --surface: #FAF6EE;
    --text: #1a1410;
    --text-2: #5b4f44;
    --text-3: #918578;
    --text-4: #b0a596;
    --border: #DDD2BD;
    --border-strong: #C4B79E;
    --accent: #C04E2D;
    --accent-bg: #FAEBE0;
    --font-serif: 'Spectral', 'Noto Serif SC', Georgia, 'Times New Roman', serif;
    --font-sans: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
  }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-serif);
    font-size: 17px;
    line-height: 1.85;
    -webkit-font-smoothing: antialiased;
    background-image: radial-gradient(circle at 1px 1px, rgba(91, 79, 68, 0.06) 1px, transparent 0);
    background-size: 28px 28px;
  }
  nav.top {
    position: sticky; top: 0;
    background: rgba(243, 238, 228, 0.85);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border);
    z-index: 100;
    padding: 14px 0;
  }
  nav.top .inner {
    max-width: 1000px; margin: 0 auto; padding: 0 36px;
    display: flex; justify-content: space-between; align-items: center;
  }
  nav.top .back {
    color: var(--text-2);
    font-family: var(--font-sans);
    font-size: 13px; font-weight: 500;
    text-decoration: none;
    display: flex; align-items: center; gap: 8px;
    transition: color 0.15s;
  }
  nav.top .back:hover { color: var(--accent); }
  nav.top .back::before { content: '←'; font-size: 16px; }
  nav.top .brand {
    font-family: var(--font-serif);
    font-weight: 600;
    font-size: 14px;
    color: var(--text-2);
  }

  main.essay {
    max-width: 960px;
    margin: 0 auto;
    padding: 60px 36px 100px;
  }
  .eyebrow {
    font-family: var(--font-sans);
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 24px;
  }
  .doc-title {
    font-family: var(--font-serif);
    font-size: clamp(28px, 3.6vw, 38px);
    font-weight: 500;
    letter-spacing: -0.018em;
    line-height: 1.25;
    color: var(--text);
    margin-bottom: 48px;
    padding-bottom: 36px;
    border-bottom: 1px solid var(--border);
  }

  .md-content > *:first-child { margin-top: 0; }
  .md-content h1 {
    font-family: var(--font-serif);
    font-size: 28px;
    font-weight: 500;
    color: var(--text);
    letter-spacing: -0.018em;
    margin: 12px 0 24px;
    line-height: 1.25;
  }
  .md-content h2 {
    font-family: var(--font-serif);
    font-size: 24px;
    font-weight: 500;
    color: var(--text);
    margin: 48px 0 16px;
    padding-top: 36px;
    border-top: 1px solid var(--border);
    letter-spacing: -0.012em;
    line-height: 1.3;
  }
  .md-content h2:first-child { padding-top: 0; border-top: none; margin-top: 0; }
  .md-content h3 {
    font-family: var(--font-serif);
    font-size: 19px;
    font-weight: 600;
    color: var(--text);
    margin: 32px 0 12px;
    letter-spacing: -0.005em;
  }
  .md-content h4 {
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    margin: 24px 0 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .md-content p {
    font-size: 16.5px;
    line-height: 1.85;
    color: var(--text-2);
    margin-bottom: 18px;
  }
  .md-content p strong, .md-content li strong { color: var(--text); font-weight: 600; }
  .md-content em { font-style: italic; color: var(--text); }
  .md-content ul, .md-content ol { padding-left: 26px; margin-bottom: 20px; }
  .md-content li {
    color: var(--text-2);
    font-size: 16.5px;
    line-height: 1.8;
    margin-bottom: 8px;
  }
  .md-content blockquote {
    border-left: 3px solid var(--accent);
    padding: 4px 0 4px 20px;
    margin: 24px 0;
    font-style: italic;
    color: var(--text);
    font-size: 17px;
  }
  .md-content blockquote p { margin-bottom: 0; }
  .md-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
    font-size: 14px;
    font-family: var(--font-sans);
  }
  .md-content thead { border-bottom: 2px solid var(--border-strong); }
  .md-content th, .md-content td {
    border-bottom: 1px solid var(--border);
    padding: 10px 16px 10px 0;
    text-align: left;
    vertical-align: top;
  }
  .md-content th {
    font-weight: 600;
    color: var(--text);
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .md-content td { color: var(--text-2); }
  .md-content code {
    background: var(--bg-2);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 13.5px;
    font-family: var(--font-mono);
    color: var(--text);
    border: 1px solid var(--border);
  }
  .md-content pre {
    background: var(--bg-2);
    border: 1px solid var(--border);
    padding: 18px 20px;
    border-radius: 6px;
    margin: 22px 0;
    font-size: 13px;
    overflow-x: auto;
    line-height: 1.7;
  }
  .md-content pre code {
    background: none;
    border: none;
    padding: 0;
    font-size: inherit;
    color: var(--text);
  }
  .md-content .wl {
    color: var(--text-3);
    border-bottom: 1px dotted var(--text-4);
    cursor: help;
    font-style: italic;
  }
  .md-content a {
    color: var(--accent);
    text-decoration: underline;
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }
  .md-content a:hover { color: var(--text); }
  .md-content hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 40px 0;
  }

  /* Obsidian callout */
  .md-content .callout {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 6px;
    padding: 20px 24px;
    margin: 24px 0;
  }
  .md-content .callout-title {
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 14px;
    letter-spacing: 0.01em;
  }
  .md-content .callout-body > *:first-child { margin-top: 0; }
  .md-content .callout-body > *:last-child { margin-bottom: 0; }
  .md-content .callout-body p {
    font-size: 15.5px;
    line-height: 1.75;
    margin-bottom: 12px;
  }
  .md-content .callout-body ol, .md-content .callout-body ul {
    margin: 8px 0 14px;
    padding-left: 22px;
  }
  .md-content .callout-body li {
    font-size: 15.5px;
    line-height: 1.7;
    margin-bottom: 6px;
  }
  .md-content .callout-info,
  .md-content .callout-summary { border-left-color: var(--accent); }
  .md-content .callout-warning,
  .md-content .callout-caution { border-left-color: var(--gold, #B8862A); }
  .md-content .callout-warning .callout-title,
  .md-content .callout-caution .callout-title { color: var(--gold, #B8862A); }
  .md-content .callout-tip,
  .md-content .callout-note { border-left-color: var(--teal, #1B4D5C); }
  .md-content .callout-tip .callout-title,
  .md-content .callout-note .callout-title { color: var(--teal, #1B4D5C); }

  footer.foot {
    padding: 36px 36px 40px;
    text-align: center;
    color: var(--text-3);
    font-size: 11.5px;
    font-family: var(--font-mono);
    border-top: 1px solid var(--border);
    letter-spacing: 0.04em;
  }
  footer.foot a { color: var(--text-3); text-decoration: none; }
  footer.foot a:hover { color: var(--accent); }

  @media (max-width: 720px) {
    main.essay { padding: 40px 24px 80px; }
    nav.top .inner { padding: 0 24px; }
  }
</style>
</head>
<body>

<nav class="top">
  <div class="inner">
    <a class="back" href="index.html" onclick="backToMain(event)">返回主站</a>
    <div class="brand">投研架构笔记</div>
  </div>
</nav>

<main class="essay">
  <div class="eyebrow">{{EYEBROW}}</div>
  <h1 class="doc-title">{{TITLE}}</h1>
  <article class="md-content">
{{CONTENT}}
  </article>
</main>

<footer class="foot">
  <a href="index.html" onclick="backToMain(event)">← 返回主站</a>
</footer>

<script>
  // 从主站进来（openDocReader 设了 sessionStorage 标记）用 history.back() 保留滚动位置；
  // 直接打开 essay（无标记）则按 href 跳到主站顶部
  function backToMain(e) {
    if (sessionStorage.getItem('cameFromMain') === '1') {
      e.preventDefault();
      window.history.back();
    }
  }
</script>

</body>
</html>
'''


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f'Building HTML pages in: {base_dir}\n')
    success = 0
    for src, dst, title, eyebrow in DOCS:
        src_path = os.path.join(base_dir, src)
        dst_path = os.path.join(base_dir, dst)
        if not os.path.exists(src_path):
            print(f'  ! missing: {src}')
            continue
        with open(src_path, 'r', encoding='utf-8') as f:
            md = f.read()
        content = render_markdown(md)
        html_out = (TEMPLATE
                    .replace('{{TITLE}}', esc(title))
                    .replace('{{EYEBROW}}', esc(eyebrow))
                    .replace('{{CONTENT}}', content))
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(html_out)
        print(f'  done {dst}  ({len(html_out):,} bytes)')
        success += 1
    print(f'\nBuilt {success}/{len(DOCS)} pages.')


if __name__ == '__main__':
    main()
