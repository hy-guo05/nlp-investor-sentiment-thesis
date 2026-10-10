# -*- coding: utf-8 -*-
"""
measure_pipeline.py — 基于年报MD&A文本的投资者情绪测度五步流水线
数据来源: 巨潮资讯网(cninfo.com.cn)公开年报文本 (2019-2025)
输出: measure_results.csv (企业-年份面板情绪得分)
依赖: 仅Python标准库 (csv, re, jieba可选 — 无jieba时使用内置备用分词)
"""
import csv
import re

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

# ---------- 第一步: 数据来源与读取 ----------
# 实际研究中此处读取 pdfplumber 提取后的 MD&A 文本;
# 本脚本内置一个可运行的最小示例数据以演示完整流水线。
SAMPLE_TEXTS = [
    {"stkcd": "000001", "year": 2024, "text": "公司坚持稳健经营，营业收入稳步增长，市场占有率持续提升，经营现金流充沛。"},
    {"stkcd": "000001", "year": 2025, "text": "公司积极拓展新业务，业绩表现良好，但也面临行业竞争加剧的风险与挑战。"},
    {"stkcd": "600519", "year": 2024, "text": "公司品牌优势显著，盈利能力突出，分红政策稳定，未来发展前景广阔。"},
    {"stkcd": "600519", "year": 2025, "text": "行业景气度提升，公司销售强劲增长，管理层对明年经营持乐观态度。"},
    {"stkcd": "000024", "year": 2024, "text": "受行业下行影响，公司销售疲软，债务压力增大，商誉减值风险突出。"},
    {"stkcd": "000024", "year": 2025, "text": "经营面临亏损，现金流紧张，管理层承认存在重大不确定性风险。"},
]

# ---------- 第二步: 词典与停用词准备 ----------
# 词典为示例子集; 完整词典来自大连理工情感本体库 + 中文金融情感词典融合
POS_WORDS = {"增长", "提升", "稳健", "充沛", "积极", "良好", "显著", "突出",
             "稳定", "广阔", "强劲", "乐观", "改善", "优异", "创新", "领先"}
NEG_WORDS = {"风险", "挑战", "疲软", "压力", "减值", "亏损", "紧张", "重大",
             "不确定", "下行", "竞争加剧", "下降", "恶化", "困难", "危机", "失败"}
NEGATE_WORDS = {"不", "未", "没有", "无", "难以"}  # 前置否定窗口=3字

STOPWORDS = {"的", "了", "和", "是", "在", "也", "对", "但", "与", "及"}

# ---------- 第三步: 文本预处理 ----------
def clean_text(t: str) -> str:
    # 保留中文, 去除数字/英文/标点; 无jieba时在词典词之间加空格便于匹配
    t = re.sub(r"[^\u4e00-\u9fff]+", " ", t).strip()
    if not HAS_JIEBA:
        all_words = sorted(POS_WORDS | NEG_WORDS, key=len, reverse=True)
        for w in all_words:
            t = t.replace(w, f" {w} ")
    return t

def tokenize(t: str):
    if HAS_JIEBA:
        words = jieba.lcut(t)
    else:
        # 备用n-gram分词: 直接用词典词匹配统计
        return t.split()
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]

# ---------- 第四步: 词典匹配与情绪打分 ----------
def sentiment_score(words):
    pos = neg = 0
    for i, w in enumerate(words):
        if w in POS_WORDS:
            # 前置否定窗口处理
            window = words[max(0, i - 3):i]
            if any(n in window for n in NEGATE_WORDS):
                neg += 1
            else:
                pos += 1
        elif w in NEG_WORDS:
            window = words[max(0, i - 3):i]
            if any(n in window for n in NEGATE_WORDS):
                pos += 1
            else:
                neg += 1
    return pos, neg, (pos - neg) / (pos + neg + 1)

# ---------- 第五步: 输出企业-年度面板 ----------
def main():
    rows = []
    for rec in SAMPLE_TEXTS:
        words = tokenize(clean_text(rec["text"]))
        pos, neg, score = sentiment_score(words)
        rows.append({"stkcd": rec["stkcd"], "year": rec["year"],
                     "pos_freq": pos, "neg_freq": neg,
                     "n_tokens": len(words), "sentiment": round(score, 4)})
    with open("measure_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["stkcd", "year", "pos_freq",
                                               "neg_freq", "n_tokens", "sentiment"])
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(r)
    print("已输出 measure_results.csv — 企业-年度面板情绪得分表")
    print("分词器:", "jieba" if HAS_JIEBA else "内置备用(词典n-gram)")

if __name__ == "__main__":
    main()
