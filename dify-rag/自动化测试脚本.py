"""
Dify RAG 自动化测试脚本
用法：
1. 在 Dify 应用页面 → 访问 API → 复制 API Key
2. 修改下面的 API_KEY 和 BASE_URL
3. 运行：python 自动化测试脚本.py
"""

import requests
import json
import csv
import time
from datetime import datetime
import os

# ==================== 配置区 ====================

# Dify API 配置（在 Dify 应用页面 → 左侧"访问 API" → 复制）
API_KEY = "your-api-key-here"  # 替换成你的 API Key
BASE_URL = "https://api.dify.ai/v1"  # Dify 云版地址，私有部署需要改

# ==================== 测试题 ====================

test_questions = [
    # 一、精确查询
    {"id": 1,  "type": "精确查询", "question": "白衬衫 MC-S001 的价格是多少？", "expected": "399元"},
    {"id": 2,  "type": "精确查询", "question": "M码的腰围范围是多少？", "expected": "66-70cm"},
    {"id": 3,  "type": "精确查询", "question": "金卡会员需要累计消费多少钱？", "expected": "2000元"},
    {"id": 4,  "type": "精确查询", "question": "退货后退款多久到账？", "expected": "1-7个工作日（根据支付方式）"},
    {"id": 5,  "type": "精确查询", "question": "你们用什么快递发货？满多少包邮？", "expected": "顺丰，满199包邮"},

    # 二、跨段落查询
    {"id": 6,  "type": "跨段落", "question": "我165cm 60kg，想买一件西装外套，推荐什么尺码和版型？", "expected": "L码，宽松版"},
    {"id": 7,  "type": "跨段落", "question": "金卡会员有哪些权益？和黑卡差在哪里？", "expected": "包含两个等级的权益对比"},
    {"id": 8,  "type": "跨段落", "question": "如果衣服有质量问题，我需要怎么做？运费谁出？", "expected": "提供照片+联系客服，运费MOXI承担"},
    {"id": 9,  "type": "跨段落", "question": "你们的衬衫和针织衫分别用什么面料？各自怎么洗？", "expected": "衬衫长绒棉/机洗，针织衫美利奴羊毛/手洗"},
    {"id": 10, "type": "跨段落", "question": "大促期间买的东西退货政策有什么不同？", "expected": "时效可能延长2-3个工作日"},

    # 三、模糊/口语化查询
    {"id": 11, "type": "模糊查询", "question": "能退吗？", "expected": "7天无理由退货"},
    {"id": 12, "type": "模糊查询", "question": "有没有大码的？", "expected": "目前S-XL，MOXI+大码系列即将推出"},
    {"id": 13, "type": "模糊查询", "question": "起球了咋办？", "expected": "抗起球处理/使用洗衣袋"},
    {"id": 14, "type": "模糊查询", "question": "怎么成为你们的VIP？", "expected": "累计消费满500/2000/5000"},
    {"id": 15, "type": "模糊查询", "question": "有实体店可以试穿吗？", "expected": "杭州和上海有体验店"},

    # 四、知识库外查询（测试幻觉控制）
    {"id": 16, "type": "知识库外", "question": "你们有男装吗？", "expected": "应该回复没有相关信息"},
    {"id": 17, "type": "知识库外", "question": "MOXI墨兮和优衣库比哪个好？", "expected": "应该回复没有相关信息"},
    {"id": 18, "type": "知识库外", "question": "能帮我推荐一个发型吗？", "expected": "应该回复没有相关信息"},
    {"id": 19, "type": "知识库外", "question": "你们的CEO是谁？年营收多少？", "expected": "应该回复没有相关信息"},
    {"id": 20, "type": "知识库外", "question": "可以货到付款吗？", "expected": "应该回复没有相关信息"},
]

# ==================== API 调用 ====================

def chat_with_dify(question: str, conversation_id: str = "", max_retries: int = 3) -> dict:
    """调用 Dify Chatflow API，带重试机制"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": "test_user",
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{BASE_URL}/chat-messages",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code != 200:
                error_detail = resp.text
                print(f"  [API错误] status={resp.status_code}, detail={error_detail}")
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    print(f"  [重试] 等待{wait}秒后重试 ({attempt+2}/{max_retries})...")
                    time.sleep(wait)
                    continue
                return {"answer": f"[ERROR] {resp.status_code}: {error_detail}", "conversation_id": "", "metadata": {}}
            data = resp.json()
            return {
                "answer": data.get("answer", ""),
                "conversation_id": data.get("conversation_id", ""),
                "metadata": data.get("metadata", {}),
            }
        except Exception as e:
            print(f"  [异常] {str(e)}")
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  [重试] 等待{wait}秒后重试 ({attempt+2}/{max_retries})...")
                time.sleep(wait)
                continue
            return {"answer": f"[ERROR] {str(e)}", "conversation_id": "", "metadata": {}}


# ==================== 评判逻辑 ====================

KEYWORDS_MAP = {
    1:  ["399"],
    2:  ["66", "70"],
    3:  ["2000"],
    4:  ["1", "7", "工作日"],
    5:  ["顺丰", "199"],
    6:  ["L"],
    7:  ["金卡", "黑卡"],
    8:  ["照片", "运费"],
    9:  ["长绒棉", "美利奴"],
    10: ["延长", "2-3"],
    11: ["7天", "无理由", "退货"],
    12: ["S", "XL"],
    13: ["起球", "洗衣袋"],
    14: ["500", "2000", "5000"],
    15: ["杭州", "上海", "体验店"],
}

def judge_answer(question_data: dict, answer: str) -> str:
    """判断回答质量"""
    q_type = question_data["type"]
    q_id = question_data["id"]

    if "[ERROR]" in answer:
        return "🔴 API错误"

    if q_type == "知识库外":
        refuse_keywords = ["没有找到", "抱歉", "暂时没有", "无法", "不确定", "没有相关", "人工客服", "无法提供", "不在"]
        if any(kw in answer for kw in refuse_keywords):
            return "✅ 正确拒答"
        else:
            return "❌ 幻觉（应该拒答但编造了答案）"
    else:
        keywords = KEYWORDS_MAP.get(q_id, [])
        if keywords:
            hit = sum(1 for kw in keywords if kw in answer)
            if hit >= len(keywords) * 0.5:
                return f"✅ 命中关键信息（{hit}/{len(keywords)}）"
        return "⚠️ 需人工核查"


# ==================== 主流程 ====================

def run_test(test_name: str = "知识库A"):
    """运行一轮测试"""
    print(f"\n{'='*60}")
    print(f"开始测试：{test_name}")
    print(f"{'='*60}\n")

    results = []
    stats = {"total": 0, "pass": 0, "fail": 0, "check": 0, "error": 0}

    for q in test_questions:
        stats["total"] += 1
        print(f"[{q['id']}/20] {q['question']}")

        # 每次用新的 conversation_id，避免多轮记忆干扰
        resp = chat_with_dify(q["question"])
        answer = resp["answer"]
        judgement = judge_answer(q, answer)

        if "✅" in judgement:
            stats["pass"] += 1
        elif "❌" in judgement:
            stats["fail"] += 1
        elif "🔴" in judgement:
            stats["error"] += 1
        else:
            stats["check"] += 1

        print(f"  回答：{answer[:100]}...")
        print(f"  判定：{judgement}\n")

        results.append({
            "题号": q["id"],
            "类型": q["type"],
            "问题": q["question"],
            "期望答案": q["expected"],
            "实际回答": answer,
            "判定": judgement,
        })

        time.sleep(3)  # 避免 API 限流

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"测试结果_{test_name}_{timestamp}"

    # 保存 CSV
    csv_path = os.path.join(os.path.dirname(__file__), "..", "test-results", f"{filename}.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # 保存 Markdown 报告
    md_path = os.path.join(os.path.dirname(__file__), "..", "test-results", f"{filename}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# RAG 测试报告 — {test_name}\n\n")
        f.write(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 总体统计\n\n")
        f.write(f"| 指标 | 数值 |\n|------|------|\n")
        f.write(f"| 总题数 | {stats['total']} |\n")
        f.write(f"| 通过 | {stats['pass']} |\n")
        f.write(f"| 失败（幻觉） | {stats['fail']} |\n")
        f.write(f"| 需人工核查 | {stats['check']} |\n")
        f.write(f"| 通过率 | {stats['pass']/stats['total']*100:.1f}% |\n\n")

        f.write(f"## 分类统计\n\n")
        for q_type in ["精确查询", "跨段落", "模糊查询", "知识库外"]:
            type_results = [r for r in results if r["类型"] == q_type]
            type_pass = sum(1 for r in type_results if "✅" in r["判定"])
            f.write(f"**{q_type}**：{type_pass}/{len(type_results)}\n\n")

        f.write(f"## 详细结果\n\n")
        f.write(f"| 题号 | 类型 | 问题 | 判定 |\n")
        f.write(f"|------|------|------|------|\n")
        for r in results:
            f.write(f"| {r['题号']} | {r['类型']} | {r['问题']} | {r['判定']} |\n")

        f.write(f"\n## 详细回答\n\n")
        for r in results:
            f.write(f"### Q{r['题号']}：{r['问题']}\n\n")
            f.write(f"- 期望：{r['期望答案']}\n")
            f.write(f"- 实际：{r['实际回答']}\n")
            f.write(f"- 判定：{r['判定']}\n\n")

    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"通过：{stats['pass']}  失败：{stats['fail']}  待核查：{stats['check']}  API错误：{stats['error']}")
    print(f"通过率：{stats['pass']/stats['total']*100:.1f}%")
    print(f"CSV 结果：{csv_path}")
    print(f"MD 报告：{md_path}")
    print(f"{'='*60}")

    return results, stats


if __name__ == "__main__":
    # ============================================
    # 使用方法：
    #
    # 第一轮：关联知识库A（固定长度），运行：
    #   test_name 改为 "知识库A-固定长度"
    #
    # 第二轮：在 Dify 里切换到知识库B（按标题），运行：
    #   test_name 改为 "知识库B-按标题"
    #
    # 第三轮（可选）：调参数后运行：
    #   test_name 改为 "知识库B-TopK5"
    # ============================================

    run_test(test_name="知识库B-补充退换货-阈值0.3")
