# -*- coding: utf-8 -*-
"""Build .docx from the thesis content using only the Python standard library.
DOCX = ZIP + OOXML. Generates an academic-formatted thesis with cover,
headings, paragraphs, tables and a reference list.
"""
import io, os, re, zipfile

OUT = os.path.join("output", "thesis-001", "stage3",
                   "基于年报文本的投资者情绪测度研究.docx")
DOCX_NAME = "基于年报文本的投资者情绪测度研究.docx"

md = io.open("thesis.md", encoding="utf-8").read()
lines = md.split("\n")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def run(text, bold=False, size=24, font="SimSun", color=None, italic=False):
    props = '<w:rPr><w:rFonts w:ascii="%s" w:eastAsia="%s" w:hAnsi="%s"/>' % (font, font, font)
    if bold:
        props += "<w:b/><w:bCs/>"
    if italic:
        props += "<w:i/>"
    if color:
        props += '<w:color w:val="%s"/>' % color
    props += '<w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr>' % (size, size)
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (props, esc(text))


def para(text, style=None, align=None, indent=False, space_after=120,
         bold=False, size=24, font="SimSun", color=None):
    ppr = "<w:pPr>"
    if style:
        ppr += '<w:pStyle w:val="%s"/>' % style
    ppr += '<w:spacing w:after="%d" w:line="360" w:lineRule="auto"/>' % space_after
    if indent:
        ppr += '<w:ind w:firstLine="480"/>'
    if align:
        ppr += '<w:jc w:val="%s"/>' % align
    ppr += "</w:pPr>"
    return "<w:p>%s%s</w:p>" % (ppr, run(text, bold=bold, size=size, font=font, color=color))


def table_xml(rows, header=True):
    """rows: list of list of str"""
    total = len(rows[0])
    grid = '<w:tblGrid>' + "".join('<w:gridCol w:w="%d"/>' % (9000 // total) for _ in range(total)) + '</w:tblGrid>'
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="4" w:color="666666"/>'
               '<w:left w:val="single" w:sz="4" w:color="666666"/>'
               '<w:bottom w:val="single" w:sz="4" w:color="666666"/>'
               '<w:right w:val="single" w:sz="4" w:color="666666"/>'
               '<w:insideH w:val="single" w:sz="4" w:color="666666"/>'
               '<w:insideV w:val="single" w:sz="4" w:color="666666"/>'
               '</w:tblBorders>')
    tblpr = '<w:tblPr><w:tblW w:w="5000" w:type="pct"/>%s</w:tblPr>' % borders
    xml = '<w:tbl>' + tblpr + grid
    for ri, r in enumerate(rows):
        is_head = header and ri == 0
        xml += '<w:tr>'
        for c in r:
            shd = '<w:shd w:val="clear" w:fill="DCE6F1"/>' if is_head else ''
            tcpr = '<w:tcPr>%s<w:vAlign w:val="center"/></w:tcPr>' % shd
            cellp = ('<w:p><w:pPr><w:spacing w:after="0" w:line="280" w:lineRule="auto"/>'
                     '<w:jc w:val="center"/></w:pPr>%s</w:p>'
                     % run(c, bold=is_head, size=19, font=("SimHei" if is_head else "SimSun")))
            xml += '<w:tc>' + tcpr + cellp + '</w:tc>'
        xml += '</w:tr>'
    return xml + '</w:tbl>'


body = []

# ---------- 封面 ----------
body.append(para("", size=24))
body.append(para("大连财经学院", align="center", bold=True, size=36, font="SimHei", color="1A3A5C"))
body.append(para("大数据与管理科学学院", align="center", bold=True, size=28, font="SimHei", color="1A3A5C"))
body.append(para("", size=24))
body.append(para("预演毕业论文", align="center", bold=True, size=44, font="SimHei"))
body.append(para("", size=24))
body.append(para("基于上市公司年报文本的投资者情绪测度构建", align="center", bold=True, size=32, font="SimHei"))
body.append(para("及其对股价波动的影响研究", align="center", bold=True, size=32, font="SimHei"))
body.append(para("", size=24))
body.append(para("——一项基于文本挖掘的五步流水线实证研究", align="center", size=24))
body.append(para("", size=24))
body.append(para("", size=24))
body.append(para("作  者：XXX", align="center", size=26))
body.append(para("专  业：数据科学与大数据技术", align="center", size=26))
body.append(para("指导教师：XXX", align="center", size=26))
body.append(para("完成日期：2026 年 10 月", align="center", size=26))
body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

# ---------- 正文解析 ----------
i = 0
n = len(lines)
para_buf = []


def flush_para():
    if para_buf:
        txt = " ".join(para_buf).strip()
        if txt:
            body.append(para(txt, indent=True))
        del para_buf[:]


while i < n:
    s = lines[i].strip()

    # table
    if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
        flush_para()
        rows = []
        hdr = [c.strip() for c in s.strip("|").split("|")]
        rows.append(hdr)
        i += 2
        while i < n and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        body.append(table_xml(rows))
        body.append(para("", size=12, space_after=60))
        continue

    # heading
    if s.startswith("#"):
        flush_para()
        lvl = 1
        while lvl <= 6 and s[lvl:lvl + 1] == "#":
            lvl += 1
        txt = s[lvl:].strip()
        if lvl == 1:
            body.append(para(txt, align="center", bold=True, size=32, font="SimHei",
                             color="1A3A5C", space_after=240))
        elif lvl == 2:
            body.append(para(txt, bold=True, size=28, font="SimHei", color="1A3A5C",
                             space_after=180))
        else:
            body.append(para(txt, bold=True, size=24, font="SimHei", space_after=140))
        i += 1
        continue

    if s == "---":
        flush_para()
        i += 1
        continue

    if s.startswith(">"):
        flush_para()
        body.append(para(s[1:].strip(), indent=False, size=22, color="33475C"))
        i += 1
        continue

    if s.startswith("$$"):
        flush_para()
        body.append(para(s.strip("$").strip(), align="center", size=24, font="Cambria Math"))
        i += 1
        continue

    if s.startswith("- ") or s.startswith("* "):
        flush_para()
        body.append(para("· " + s[2:], indent=False, size=24))
        i += 1
        continue
    m = re.match(r"^(\d+)\.\s+(.*)$", s)
    if m:
        flush_para()
        body.append(para("%s. %s" % (m.group(1), m.group(2)), indent=False, size=24))
        i += 1
        continue

    if s == "":
        flush_para()
        i += 1
        continue

    para_buf.append(s)
    i += 1

flush_para()

document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>' + "".join(body) +
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1418" w:bottom="1440" w:left="1701" w:header="851" w:footer="992" w:gutter="0"/>'
            '</w:sectPr></w:body></w:document>')

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                 '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                 '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>')

DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:docDefaults><w:rPrDefault><w:rPr>'
          '<w:rFonts w:ascii="SimSun" w:eastAsia="SimSun" w:hAnsi="SimSun"/>'
          '<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault></w:docDefaults>'
          '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
          '<w:name w:val="Normal"/></w:style></w:styles>')

CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>基于上市公司年报文本的投资者情绪测度构建及其对股价波动的影响研究</dc:title>'
        '<dc:creator>XXX</dc:creator><cp:lastModifiedBy>XXX</cp:lastModifiedBy>'
        '</cp:coreProperties>')

APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
       '<Application>WorkBuddy</Application></Properties>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", RELS)
    z.writestr("word/document.xml", document)
    z.writestr("word/_rels/document.xml.rels", DOC_RELS)
    z.writestr("word/styles.xml", STYLES)
    z.writestr("docProps/core.xml", CORE)
    z.writestr("docProps/app.xml", APP)

print("DOCX OK:", OUT, os.path.getsize(OUT), "bytes")
