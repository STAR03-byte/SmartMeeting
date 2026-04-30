"""AI 聊天系统 prompt 构建。"""

_BASE_SYSTEM_PROMPT: str = """你是 SmartMeeting 的 AI 助理，帮助用户管理会议和任务。

重要提示：用户已通过界面选择了以下真实数据，这些数据来自 SmartMeeting 数据库，你有权访问并基于这些数据回答用户问题。不要说自己无法访问数据。"""

_ANSWER_REQUIREMENTS: str = (
    "\n\n回答要求："
    "\n1. 先基于真实结构化数据回答，不要空泛。"
    "\n2. 如果已经有任务/会议数据，就直接引用，不要要求用户重复说明。"
    "\n3. 如果用户问执行建议，请结合会议摘要、任务状态和上下文给出下一步动作。"
    "\n4. 严禁补充数据库中不存在的议程、参会人、决议、任务、时间和地点。"
    "\n5. 如果某字段缺失，必须明确说'当前没有记录到'，不要自行推断或编造。"
    "\n6. 回答尽量简洁、明确、可执行。"
)

_CONTEXT_KEY_BUILDERS: dict[str, str] = {
    "meeting_title": "\n\n【当前关联会议】\n标题：{value}",
    "meeting_description": "\n描述：{value}",
    "task_title": "\n\n【当前关联任务】\n标题：{value}",
    "task_description": "\n描述：{value}",
    "task_status": "\n状态：{value}",
    "task_priority": "\n优先级：{value}",
    "task_not_found": "\n\n注意：{value}",
    "assistant_intent": "\n\n【当前问题类型】\n{value}",
    "my_tasks": "\n\n【我的任务查询结果】\n{value}",
    "recent_meetings": "\n\n【最近相关会议】\n{value}",
    "meeting_summary": "\n\n【会议摘要】\n{value}",
    "meeting_summary_missing": "\n\n【会议摘要】\n{value}",
    "meeting_tasks": "\n\n【会议任务】\n{value}",
    "meeting_tasks_missing": "\n\n【会议任务】\n{value}",
    "meeting_participants": "\n\n【参会人员】\n{value}",
    "meeting_participants_missing": "\n\n【参会人员】\n{value}",
    "meeting_transcript_preview": "\n\n【会议转写片段】\n{value}",
    "meeting_transcript_missing": "\n\n【会议转写】\n{value}",
    "meeting_not_found": "\n\n注意：{value}",
    "meeting_description_missing": "\n\n【会议描述】\n{value}",
}


def build_chat_system_prompt(context_info: dict[str, str] | None = None) -> str:
    """构建多轮对话的 system prompt。

    包含基础角色设定、上下文信息注入和回答要求。
    """
    prompt = _BASE_SYSTEM_PROMPT

    if context_info:
        for key, template in _CONTEXT_KEY_BUILDERS.items():
            if key in context_info:
                prompt += template.format(value=context_info[key])

    prompt += _ANSWER_REQUIREMENTS
    return prompt
