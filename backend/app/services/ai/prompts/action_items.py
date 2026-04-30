"""行动项提取 prompt。"""


def build_action_items_system_prompt(participants_context: str = "") -> str:
    """构建单段转写行动项提取的 system prompt。"""
    return (
        "你是一个任务提取助手。从会议转写中提取行动项/任务。\n\n"
        "只提取明确、可执行、可落地的任务，不要把讨论语气、模糊建议、时间判断、口语化表达当成任务。\n"
        "像'后天完成也可以'、'那这个事情明天完成也可以'、'我觉得可以'这类句子不是任务，必须忽略。\n\n"
        "输出格式：JSON数组，每个任务包含：\n"
        "- title: 任务标题（简洁，不超过50字）\n"
        "- description: 任务详细描述\n"
        "- assignee_name: 负责人姓名（如果能从内容推断，否则为null）\n"
        "- priority: 优先级（high/medium/low）\n"
        "- due_hint: 截止时间提示（如果提到，否则为null）\n\n"
        "示例输出：\n"
        '[{"title": "完成项目报告", "description": "下周一前提交项目进度报告", '
        '"assignee_name": "张三", "priority": "high", "due_hint": "下周一"}]\n\n'
        f"只输出JSON数组，不要其他内容。{participants_context}"
    )


def build_action_items_user_prompt(transcript_content: str) -> str:
    """构建单段转写行动项提取的 user prompt。"""
    return f"从以下会议转写中提取所有行动项：\n\n{transcript_content}\n\n输出JSON数组："


def build_action_items_batch_system_prompt(participants_context: str = "") -> str:
    """构建多段转写批量行动项提取的 system prompt。"""
    return (
        "你是一个任务提取助手。从多段会议转写中提取行动项/任务。\n\n"
        "只提取明确、可执行、可落地的任务，不要把讨论语气、模糊建议、时间判断、口语化表达当成任务。\n"
        "输出格式：JSON数组，每个任务包含：\n"
        "- segment_index: 任务来源的转写序号（必须对应输入中的 [0]、[1]...）\n"
        "- title: 任务标题（简洁，不超过50字）\n"
        "- description: 任务详细描述\n"
        "- assignee_name: 负责人姓名（如果能从内容推断，否则为null）\n"
        "- priority: 优先级（high/medium/low）\n"
        "- due_hint: 截止时间提示（如果提到，否则为null）\n\n"
        "示例输出：\n"
        '[{"segment_index": 0, "title": "完成项目报告", "description": "下周一前提交项目进度报告", '
        '"assignee_name": "张三", "priority": "high", "due_hint": "下周一"}]\n\n'
        f"只输出JSON数组，不要其他内容。{participants_context}"
    )


def build_action_items_batch_user_prompt(numbered_transcripts: list[str]) -> str:
    """构建多段转写批量行动项提取的 user prompt。"""
    return "从以下多段会议转写中提取所有行动项：\n\n" + "\n\n".join(numbered_transcripts) + "\n\n输出JSON数组："
