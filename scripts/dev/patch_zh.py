import re

extra_common = """
    all: '全部',
    search: '搜索',
    filter: '筛选',
    reset: '重置',
    keyword: '关键词',
    searchPlaceholder: '搜索标题/描述',
    uploadFailed: '上传失败',
    sort: '排序',"""

extra_meeting = """
    locationOptional: '会议地点（可选）',
    location: '地点',
    noOrganizer: '暂无可选组织者，请先创建用户',
    createSuccess: '会议创建成功',
    createFailed: '创建失败',
    deleteSuccess: '会议已删除',
    deleteFailed: '删除失败',
    selectStartTime: '选择开始时间',
    selectEndTime: '选择结束时间',
    titlePlaceholder: '请输入会议标题',
    descriptionPlaceholder: '请输入会议描述（可选）',
    team: '所属团队',"""

extra_team = """
    selectTeamOptional: '选择团队（可选）',
    selectTeam: '选择团队',"""

extra_task = """
    meeting: '所属会议',
    reminder: '提醒',
    searchPlaceholder: '搜索任务标题',
    sortCreatedDesc: '按创建时间（新→旧）',
    sortDueAsc: '按截止时间（近→远）',
    sortDueDesc: '按截止时间（远→近）',"""

extra_participant = """
    addFailed: '添加参与者失败',
    selectParticipantOptional: '选择参与人员（可选）',"""

extra_transcript = """
    success: '转写成功',"""

with open('frontend/src/locales/zh-CN.ts', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("goToLogin: '去登录'", "goToLogin: '去登录',\n" + extra_common)
content = content.replace("endTime: '结束时间'", "endTime: '结束时间',\n" + extra_meeting)
content = content.replace("createSuccess: '团队创建成功'", "createSuccess: '团队创建成功',\n" + extra_team)
content = content.replace("priorityLow: '低'", "priorityLow: '低',\n" + extra_task)
content = content.replace("statusAttended: '已参加'", "statusAttended: '已参加',\n" + extra_participant)
content = content.replace("recordingStatus: '录音状态',", "recordingStatus: '录音状态',\n" + extra_transcript)

with open('frontend/src/locales/zh-CN.ts', 'w', encoding='utf-8') as f:
    f.write(content)
