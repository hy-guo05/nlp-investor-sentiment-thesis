# -*- coding: utf-8 -*-
"""thesis.md -> academic HTML (simple line-based state machine)"""
import io, os, re

SRC = "thesis.md"
OUTDIR = os.path.join("output", "thesis-001", "stage2")
OUT = os.path.join(OUTDIR, "formatted-thesis.html")

lines = io.open(SRC, encoding="utf-8").read().split("\n")

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(s):
    s = esc(s)
    s = s.replace("**", "\x01")
    parts = s.split("\x01")
    res = []
    for idx, p in enumerate(parts):
        res.append("<strong>" + p + "</strong>" if idx % 2 == 1 else p)
    return "".join(res)

out = []
para = []
i = 0
n = len(lines)

def flush():
    if para:
        out.append("<p>" + inline(" ".join(para)) + "</p>")
        del para[:]

while i < n:
    ln = lines[i]
    s = ln.strip()

    # table block
    if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
        flush()
        hdr = [c.strip() for c in s.strip("|").split("|")]
        out.append("<table><thead><tr>" + "".join("<th>" + inline(h) + "</th>" for h in hdr) + "</tr></thead><tbody>")
        i += 2
        while i < n and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            out.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in cells) + "</tr>")
            i += 1
        out.append("</tbody></table>")
        continue

    # heading
    if s.startswith("#"):
        flush()
        lvl = 1
        while lvl <= 6 and s[lvl:lvl + 1] == "#":
            lvl += 1
        out.append("<h%d>%s</h%d>" % (lvl, inline(s[lvl:].strip()), lvl))
        i += 1
        continue

    # hr
    if s == "---":
        flush()
        out.append("<hr/>")
        i += 1
        continue

    # blockquote
    if s.startswith(">"):
        flush()
        out.append("<blockquote>" + inline(s[1:].strip()) + "</blockquote>")
        i += 1
        continue

    # formula
    if s.startswith("$$"):
        flush()
        out.append('<p class="formula">' + esc(s.strip("$").strip()) + "</p>")
        i += 1
        continue

    # list item
    if s.startswith("- ") or s.startswith("* "):
        flush()
        out.append("<li>" + inline(s[2:]) + "</li>")
        i += 1
        continue
    m = re.match(r"^(\d+)\.\s+(.*)$", s)
    if m:
        flush()
        out.append("<li>" + inline(m.group(2)) + "</li>")
        i += 1
        continue

    if s == "":
        flush()
        i += 1
        continue

    para.append(s)
    i += 1

flush()

# post-process: wrap consecutive <li> into lists
body = "\n".join(out)
body = re.sub(r"(<li>.*?</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", body, flags=re.S)

CSS = """
@page{size:A4;margin:2.5cm;}
body{font-family:"SimSun","Songti SC","Noto Serif SC",serif;font-size:12pt;line-height:1.85;
color:#1a1a1a;max-width:800px;margin:0 auto;padding:40px 32px;background:#fff;text-align:justify;}
h1{font-family:"SimHei","Heiti SC",sans-serif;font-size:19pt;text-align:center;line-height:1.6;margin:0 0 22px;}
h2{font-family:"SimHei",sans-serif;font-size:15pt;margin:30px 0 12px;padding-bottom:5px;
border-bottom:2px solid #1a3a5c;color:#1a3a5c;}
h3{font-family:"SimHei",sans-serif;font-size:13pt;margin:20px 0 9px;color:#24405e;}
h4{font-family:"SimHei",sans-serif;font-size:12pt;margin:14px 0 7px;}
p{margin:0 0 11px;text-indent:2em;}
p.formula{text-indent:0;text-align:center;font-family:"Cambria Math",serif;font-size:13pt;
background:#f5f8fb;border-left:3px solid #1a3a5c;padding:11px 15px;margin:13px 0;color:#14283d;}
blockquote{margin:13px 0;padding:9px 16px;background:#f5f8fb;border-left:3px solid #6c8fb0;color:#33475c;text-indent:0;}
table{width:100%;border-collapse:collapse;margin:15px 0;font-size:10.5pt;}
th{background:#1a3a5c;color:#fff;font-family:"SimHei",sans-serif;padding:8px;border:1px solid #16324f;text-align:center;}
td{padding:7px 9px;border:1px solid #b9c9d8;text-align:center;}
tbody tr:nth-child(even){background:#f5f8fb;}
ul{margin:9px 0 13px;padding-left:2.2em;}li{margin:4px 0;}
hr{border:none;border-top:1px solid #c9d6e2;margin:24px 0;}
strong{font-weight:700;color:#10243a;}
"""

html = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/>'
        '<title>基于上市公司年报文本的投资者情绪测度构建及其对股价波动的影响研究</title>'
        '<style>' + CSS + '</style></head><body>' + body + '</body></html>')

os.makedirs(OUTDIR, exist_ok=True)
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK", OUT, len(html))
