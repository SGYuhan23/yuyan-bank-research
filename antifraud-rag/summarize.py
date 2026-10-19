from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
retrieval=json.loads((ROOT/'eval/retrieval-results.json').read_text())['results']
lines=['# 实际评测记录','', '这是开发用小样本评测，非独立人类盲评。参考要点单独保存在eval/cases.json，不进入生产检索。模型评审与作者发现分开记录。','', '## 检索','', '|方法|成功执行查询|有参考相关资料的查询|Recall@3均值|', '|---|---:|---:|---:|']
for mode in ['bm25','semantic']:
 rows=[r for r in retrieval if r['mode']==mode];valid=[r['recall_at_3'] for r in rows if r.get('recall_at_3') is not None];lines.append(f'|{mode}|{sum(not r.get("error") for r in rows)}/{len(rows)}|{len(valid)}|{sum(valid)/len(valid):.3f}|')
lines+=['','5个完整单元、k=3，语义检索使用实际text-embedding-v4（1024维）。10个正向相关资料题，1个资料不足题；部分题共享主题，不能视为广泛泛化测试。两种方法在该早期集合没有召回差异，当时默认选择BM25；本轮口语反例验证后默认改为BM25无命中转semantic，见CLOSEOUT.md。不添加混合排序或重排。召回不是回答准确率，资料不足题是否拒答另测。','','## 回答与修复','', '|批次|题数|流程完成|失败|模型评审支持的已完成回答|','|---|---:|---:|---:|---:|']
for name in ['answer-results.json','answer-results-repair.json','answer-results-v3.json','answer-results-final.json','answer-results-supplier-repair.json','answer-results-release.json','answer-results-scope-repair.json','answer-results-handoff.json','answer-results-supplier-handoff.json']:
 p=ROOT/'eval'/name
 if not p.exists():continue
 rows=json.loads(p.read_text())['results'];complete=sum(r['status']=='completed' for r in rows);support=sum((r.get('checks') or {}).get('supported') is True for r in rows)
 lines.append(f'|{name}|{len(rows)}|{complete}|{len(rows)-complete}|{support}|')
lines+=['','批次不能合并成总体准确率：修复批次是针对失败题的选择性复测。流程完成只表示校验通过，不表示语义正确。同一Qwen模型做生成和评审，有明显漏判；没有人工标注准确率、效率提升或银行业务收益指标。','','### 已观察到的问题与改动','', '1. 首次知识问答丢掉“对方称未收到款”的前提，并把“可能连接骗子”写成“实则接入”。同模型评审漏判。添加定向条件检查，最多修订一次，未通过则失败。','2. 首轮培训出现没有依据的小额试支付追问，并借用官方案例企业名称。增加输出检查，使用企业A/供应商B等虚构占位称谓。','3. 首轮统计题把程序公式放入原文引用，校验拒绝；中间修订仍出现省略号拼接。改为模型选择单元ID，程序附完整原文章节，计算另有输入、公式和结果。','4. 首轮越权要求安全保证时只拒绝，没有提供可回答的核实办法。修订充分性提示，区分无法保证安全与仍可提供公开核实步骤。','5. 作者复核v3发现措辞仍有风险：supplier用“仅当…才需”容易被理解为排他性规则；training把“暂停向变更账户付款”泛化成“暂停任何付款”。随后添加有日志的来源特定条件修正规则，并对两任务复测；又发现风险描述可能把猜测说成事实，补充阻断检查。此类定向修复不证明一般语义可靠性，材料始终待人工审核。','','### 反例与验证边界','', '合法供应商更换账户、截图不等于到账、专业网页/注册不等于邀约真实、全国数据不能推个体、用户要求无依据保证安全、资料注入指令均有实际题目与运行。冲突测试使用明确标注的合成资料与官方指引相反，未伪造两个真实官方机构发生冲突；仍需扩展真实跨版本/跨地区冲突样本。恶意指令仅在eval fixture中，生产资料没有被污染。','','模型依据支持判定可能漏判；当前“11题”规模只用于证明可执行流程并暴露错误。所有输出须复核。']
lines+=['','最新场景与适用范围修复另见[SCOPE_CLOSEOUT.md](SCOPE_CLOSEOUT.md)。','','## 本轮收尾验证','','真实embedding、五项默认流程、mock故障与金额口径参考检查见[CLOSEOUT.md](CLOSEOUT.md)。历史结果不重写；小样本不作为回答准确率。']
(ROOT/'docs/EVALUATION.md').write_text('\n'.join(lines)+'\n')
rows=json.loads((ROOT/'data/source-index.json').read_text());lines=['# 官方来源索引','', '来源初期独立发现；后来已比对材料包10个入口，详见PACKAGE_RECONCILIATION.md。生产范围仍为以下5个单元。','', '|ID|来源|类型|发布/更新|获取时间|哈希口径|','|---|---|---|---|---|---|']
for s in rows:lines.append(f"|{s['source_id']}|[{s['title']}]({s['url']})|{s['material_type']}|{s['published_or_updated_at'] or '未知'}|{s['retrieved_at']}|{s.get('hash_scope','original_http_html')}|")
(ROOT/'docs/SOURCES.md').write_text('\n'.join(lines)+'\n')
