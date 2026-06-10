from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Tuple

from app.schemas.buffer_schemas import (
    EmergencyShieldResponse,
    GeneratePrepResponse,
    ShareVersion,
    TranslateShareResponse,
)


def current_week_id() -> str:
    year, week, _ = date.today().isocalendar()
    return f"{year}-W{week:02d}"


def current_season_hint() -> str:
    month = datetime.now().month
    if month in (1, 2):
        return "春节/年初，亲友比较和催婚概率高"
    if month in (3, 4):
        return "春季换工作窗口，工作稳定性push概率中等"
    if month in (5, 6):
        return "年中节点，工作、健康和相亲话题容易出现"
    if month in (7, 8):
        return "夏季暑热，健康关心和抱怨概率中等"
    if month in (9, 10):
        return "秋季家庭聚会增多，比较和婚恋话题概率中等"
    return "年底总结期，工作、存钱、婚恋规划容易被追问"


SHIELD_BANK = {
    "marriage": {
        "scene": "你看人家小李都结婚/二胎了，你也该抓紧了。",
        "reason": "婚恋是父母最常用的焦虑出口，遇到亲友消息或节日节点时更容易出现。",
        "shields": {
            "transfer": {"text": "嗯他们挺快的。爸，你最近身体怎么样？", "anchor": "先承认听见，再把话题带回可聊的生活信息。"},
            "boundary": {"text": "我知道你们着急，但这件事我会按自己的节奏来。", "anchor": "表达理解不等于交出决定权，边界可以温和但清楚。"},
            "echo": {"text": "嗯，我知道你是担心我。", "anchor": "只接住担心，不进入辩论，能把能量消耗降到最低。"},
        },
    },
    "compare": {
        "scene": "别人家孩子工作稳定、成家也早，你要多学学。",
        "reason": "比较型push通常用别人家的进度包装成建议，实际是在表达不确定感。",
        "shields": {
            "transfer": {"text": "他们挺不容易的。你最近钓鱼/散步了吗？", "anchor": "不评价自己，也不贬低别人，直接退出比较赛道。"},
            "boundary": {"text": "每个人情况不一样，我现在的安排也有我的考虑。", "anchor": "把话题从输赢比较拉回个体差异，关系不会因此被攻击。"},
            "echo": {"text": "嗯，你希望我过得稳一点。", "anchor": "翻译出他的期待，但不承诺按他的方案行动。"},
        },
    },
    "complain": {
        "scene": "这个社会太难了/工作太累了/身体又不舒服。",
        "reason": "抱怨型沟通容易在通话中占据大量情绪空间，需要听见但不接管。",
        "shields": {
            "transfer": {"text": "是挺不容易的。那你今天吃得怎么样？", "anchor": "给一点回应后转向具体生活，避免被拖进情绪漩涡。"},
            "boundary": {"text": "我听到了，但这个我也解决不了，咱们先说点轻松的。", "anchor": "承认他的感受，同时不把自己变成情绪垃圾桶。"},
            "echo": {"text": "嗯，是挺难的。", "anchor": "低投入回应不是敷衍，是保护本次通话可持续。"},
        },
    },
    "control": {
        "scene": "你应该换个稳定工作/考公务员/按我说的做。",
        "reason": "控制型建议常来自父亲对风险的恐惧，越解释越容易被要求答辩。",
        "shields": {
            "transfer": {"text": "我会想想。爸你当年工作最难的时候怎么过的？", "anchor": "把命令改成经验分享，让他从控制者转成讲述者。"},
            "boundary": {"text": "我知道你为我好，但工作选择我会自己负责。", "anchor": "感谢动机，拒绝接收命令，边界清晰且不伤人。"},
            "echo": {"text": "嗯，你是希望我更稳定。", "anchor": "只复述需求，不解释计划，避免进入答辩模式。"},
        },
    },
}


def generate_prep(dread: int, father_type: List[str] | None = None, last_call_topics: str | None = None) -> GeneratePrepResponse:
    father_type = father_type or ["push", "complain", "compare"]
    priority = ["marriage", "control", "compare", "complain"]
    if "complain" in father_type:
        priority.insert(1, "complain")
    if "compare" in father_type:
        priority.insert(1, "compare")

    seen = []
    predictions = []
    for push_type in priority:
        if push_type in seen or push_type not in SHIELD_BANK:
            continue
        seen.append(push_type)
        item = SHIELD_BANK[push_type]
        probability = "high" if len(predictions) == 0 or dread >= 7 else "medium"
        if len(predictions) == 2:
            probability = "low" if dread <= 4 else "medium"
        reason = item["reason"]
        if last_call_topics:
            reason += f" 上次提到“{last_call_topics}”，本周可能延续。"
        predictions.append({
            "scene": item["scene"],
            "type": push_type,
            "probability": probability,
            "reason": f"{reason} 当前节点：{current_season_hint()}。",
            "shields": item["shields"],
        })
        if len(predictions) == 3:
            break

    mode = "能量守恒模式" if dread >= 7 else "温和边界模式" if dread >= 4 else "轻量连接模式"
    return GeneratePrepResponse(
        weekId=current_week_id(),
        energyMode=mode,
        predictions=predictions,
        energySupply="这通电话最多30分钟。你可以只听见、不解释、不接招；维持关系是选择，不是被审问的义务。",
    )


def sanitize_raw_share(raw_text: str) -> str:
    replacements = {
        "崩溃": "有点累",
        "抑郁": "状态有点低",
        "撑不住": "需要休息一下",
        "累瘫了": "挺累的",
        "烦死了": "有点烦",
        "绝望": "压力有点大",
    }
    text = raw_text.strip()
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def trim_text(text: str, limit: int = 50) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "~"


def translate_share(raw_text: str, style: str = "safe") -> TranslateShareResponse:
    clean = sanitize_raw_share(raw_text)
    prefix = "" if clean.startswith(("这周", "本周", "最近", "今天", "昨天", "周末")) else "这周"
    versions: Dict[str, ShareVersion] = {
        "safe": ShareVersion(
            text=trim_text(f"{prefix}{clean}，不过我会安排时间休息，周末回血一下。"),
            parentReaction="可能提醒你别太累，或顺势给建议。",
            replyAdvice="可以只回：嗯嗯，我会注意休息的。",
        ),
        "heart": ShareVersion(
            text=trim_text(f"{prefix}{clean}，有点不容易，但跟你们说一声就觉得有人惦记。"),
            parentReaction="可能会关心你，也可能不知道怎么接情绪。",
            replyAdvice="如果对方push，回：我知道你担心，我会照顾好自己。",
        ),
        "mini": ShareVersion(
            text=trim_text(f"{prefix}{clean}，累但还稳。"),
            parentReaction="大概率只收到简短关心或建议。",
            replyAdvice="不想展开时回：嗯嗯，放心。",
        ),
    }
    selected = versions.get(style, versions["safe"])
    return TranslateShareResponse(versions=versions, selected=selected)


KEYWORDS: List[Tuple[str, str, float]] = [
    ("marriage", "结婚|对象|相亲|二胎|孙子|孙女|成家|老了谁照顾", 0.92),
    ("compare", "别人家|人家|小李|同学|邻居|都已经|你看看", 0.86),
    ("control", "应该|必须|听话|考公务员|换工作|按我说|稳定", 0.84),
    ("health", "身体|血压|生病|医院|养老|健康", 0.78),
    ("complain", "社会|太难|不公平|累|烦|抱怨|没意思", 0.74),
]


def detect_push_type(text: str) -> Tuple[str, float]:
    import re

    for push_type, pattern, confidence in KEYWORDS:
        if re.search(pattern, text):
            return push_type, confidence
    return "other", 0.55


def emergency_shield(father_text: str) -> EmergencyShieldResponse:
    detected_type, confidence = detect_push_type(father_text)
    bank = SHIELD_BANK.get(detected_type) or SHIELD_BANK["control"]
    responses = [
        {"type": "transfer", "text": bank["shields"]["transfer"]["text"][:15]},
        {"type": "boundary", "text": bank["shields"]["boundary"]["text"][:15]},
        {"type": "echo", "text": bank["shields"]["echo"]["text"][:15]},
    ]
    return EmergencyShieldResponse(
        detectedType=detected_type,
        confidence=confidence,
        responses=responses,
        reminder="注意：你正在进入消耗区。可以低能耗嗯嗯、温和设界，或找理由结束通话。",
    )
