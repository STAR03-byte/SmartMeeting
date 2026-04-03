import os
import re

VUE_FILES_DIR = "D:\\SmartMeeting\\frontend\\src"

replacements = {
    # App.vue
    "'已登录'": "$t('common.loggedIn')",
    "'管理员'": "$t('team.roleAdmin')",
    "'成员'": "$t('team.roleMember')",
    ">仪表盘<": ">{{ $t('app.navDashboard') }}<",
    ">会议列表<": ">{{ $t('app.navMeetings') }}<",
    ">任务中心<": ">{{ $t('app.navTasks') }}<",
    ">热词设置<": ">{{ $t('app.navHotwords') }}<",
    ">退出登录<": ">{{ $t('common.logout') }}<",
    ">去登录<": ">{{ $t('common.goToLogin') }}<",
    
    # Common
    ">确认<": ">{{ $t('common.confirm') }}<",
    ">取消<": ">{{ $t('common.cancel') }}<",
    ">保存<": ">{{ $t('common.save') }}<",
    ">删除<": ">{{ $t('common.delete') }}<",
    ">编辑<": ">{{ $t('common.edit') }}<",
    ">创建<": ">{{ $t('common.create') }}<",
    ">添加<": ">{{ $t('common.add') }}<",
    ">刷新<": ">{{ $t('common.refresh') }}<",
    ">返回<": ">{{ $t('common.back') }}<",
    "label=\"操作\"": ":label=\"$t('common.operations')\"",
    "label=\"状态\"": ":label=\"$t('common.status')\"",
    ">关闭<": ">{{ $t('common.close') }}<",
    ">查看<": ">{{ $t('common.view') }}<",
    "label=\"描述\"": ":label=\"$t('common.description')\"",
    "'未知'": "t('common.unknown')",
    
    # Dashboard
    ">高效会议管理，智能任务追踪<": ">{{ $t('dashboard.slogan') }}<",
    ">新建会议<": ">{{ $t('dashboard.newMeeting') }}<",
    ">会议总数<": ">{{ $t('dashboard.totalMeetings') }}<",
    ">进行中<": ">{{ $t('meeting.statusOngoing') }}<",
    ">计划中<": ">{{ $t('meeting.statusPlanned') }}<",
    ">已结束<": ">{{ $t('meeting.statusDone') }}<",
    ">近期会议<": ">{{ $t('dashboard.recentMeetings') }}<",
    ">查看全部<": ">{{ $t('dashboard.viewAll') }}<",
    "description=\"暂无会议数据\"": ":description=\"$t('dashboard.noMeetingData')\"",
    ">快捷操作<": ">{{ $t('dashboard.quickActions') }}<",
    ">任务管理<": ">{{ $t('dashboard.taskManagement') }}<",
    ">用户管理<": ">{{ $t('dashboard.userManagement') }}<",
    "\"早上好\"": "t('dashboard.morning')",
    "\"下午好\"": "t('dashboard.afternoon')",
    "\"晚上好\"": "t('dashboard.evening')",
    "\"计划中\"": "t('meeting.statusPlanned')",
    "\"进行中\"": "t('meeting.statusOngoing')",
    "\"已结束\"": "t('meeting.statusDone')",
    "\"已取消\"": "t('meeting.statusCancelled')",

    # Teams
    ">我的团队<": ">{{ $t('team.title') }}<",
    ">创建团队<": ">{{ $t('team.createTeam') }}<",
    "label=\"团队名称\"": ":label=\"$t('team.teamName')\"",
    "label=\"我的角色\"": ":label=\"$t('team.myRole')\"",
    "'加载团队列表失败'": "t('team.loadFailed')",
    "'所有者'": "t('team.roleOwner')",
    # "'管理员'": "t('team.roleAdmin')", # handled
    # "'成员'": "t('team.roleMember')", # handled
    ">团队详情<": ">{{ $t('team.detailTitle') }}<",
    ">基本信息<": ">{{ $t('team.basicInfo') }}<",
    ">暂无描述<": ">{{ $t('team.noDescription') }}<",
    "label=\"创建时间\"": ":label=\"$t('team.createdAt')\"",
    ">成员管理<": ">{{ $t('team.memberManagement') }}<",
    ">添加成员<": ">{{ $t('team.addMember') }}<",
    "label=\"姓名\"": ":label=\"$t('team.memberName')\"",
    "label=\"邮箱\"": ":label=\"$t('team.email')\"",
    "label=\"角色\"": ":label=\"$t('team.role')\"",
    "label=\"加入时间\"": ":label=\"$t('team.joinedAt')\"",
    "title=\"确定要移除该成员吗？\"": ":title=\"$t('team.removeConfirm')\"",
    ">移除<": ">{{ $t('team.remove') }}<",
    "title=\"添加成员\"": ":title=\"$t('team.addMemberTitle')\"",
    "label=\"选择用户\"": ":label=\"$t('team.selectUser')\"",
    "'请选择用户'": "t('team.selectUserRequired')",
    "placeholder=\"请选择要添加的用户\"": ":placeholder=\"$t('team.selectUserPlaceholder')\"",
    "'请选择角色'": "t('team.roleRequired')",
    ">确认添加<": ">{{ $t('team.confirmAdd') }}<",
    "'加载团队信息失败'": "t('team.loadTeamFailed')",
    "'加载成员列表失败'": "t('team.loadMemberFailed')",
    "'加载用户列表失败'": "t('team.loadUserFailed')",
    "'添加成员成功'": "t('team.addMemberSuccess')",
    "'添加成员失败'": "t('team.addMemberFailed')",
    "'成员已移除'": "t('team.memberRemoved')",
    "'移除成员失败'": "t('team.removeMemberFailed')",
    "'角色更新成功'": "t('team.roleUpdateSuccess')",
    "'角色更新失败'": "t('team.roleUpdateFailed')",
    "'请输入团队名称'": "t('team.teamNameRequired')",
    "'长度在 2 到 50 个字符'": "t('team.teamNameLength')",
    "placeholder=\"请输入团队描述（可选）\"": ":placeholder=\"$t('team.teamDescriptionPlaceholder')\"",
    "'团队创建成功'": "t('team.createSuccess')",

    # Meetings
    "title=\"确认删除此会议？\"": ":title=\"$t('meeting.deleteConfirm')\"",
    "content=\"会议工作台\"": ":content=\"$t('meeting.workbench')\"",
    "组织者：": "{{ $t('meeting.organizer') }}：",
    "状态：": "{{ $t('common.status') }}：",
    ">生成分享链接<": ">{{ $t('meeting.generateShareLink') }}<",
    ">邮件分发<": ">{{ $t('meeting.emailDistribute') }}<",
    ">新建任务<": ">{{ $t('meeting.newTask') }}<",
    "\"会议ID无效\"": "t('meeting.invalidMeetingId')",
    "\"分享链接已生成并复制\"": "t('meeting.shareLinkGenerated')",
    "\"分享链接已复制\"": "t('meeting.shareLinkCopied')",
    "\"会议纪要\"": "t('meeting.meetingSummary')",
    "\"已打开邮件客户端\"": "t('meeting.emailClientOpened')",
    "label=\"会议标题\"": ":label=\"$t('meeting.title')\"",
    "label=\"会议描述\"": ":label=\"$t('meeting.description')\"",
    "label=\"开始时间\"": ":label=\"$t('meeting.startTime')\"",
    "label=\"结束时间\"": ":label=\"$t('meeting.endTime')\"",

    # Hotwords
    ">热词管理<": ">{{ $t('hotword.title') }}<",
    ">维护个人热词，提升 Whisper 转写准确率。<": ">{{ $t('hotword.description') }}<",
    ">新增热词<": ">{{ $t('hotword.addHotword') }}<",
    "label=\"热词\"": ":label=\"$t('hotword.hotword')\"",
    "placeholder=\"输入热词，例如项目名、人名\"": ":placeholder=\"$t('hotword.hotwordPlaceholder')\"",
    ">添加热词<": ">{{ $t('hotword.add') }}<",
    ">热词列表<": ">{{ $t('hotword.list') }}<",
    "title=\"确认删除此热词？\"": ":title=\"$t('hotword.deleteConfirm')\"",
    "\"加载热词失败\"": "t('hotword.loadFailed')",
    "\"请输入热词\"": "t('hotword.inputRequired')",
    "\"热词已添加\"": "t('hotword.addSuccess')",
    "\"已删除\"": "t('hotword.deleteSuccess')",

    # Transcripts
    ">转写片段<": ">{{ $t('transcript.title') }}<",
    "description=\"暂无转写内容\"": ":description=\"$t('transcript.empty')\"",
    "title=\"确认删除该转写片段？\"": ":title=\"$t('transcript.deleteConfirm')\"",
    ">录音文件<": ">{{ $t('transcript.audioRecordTitle') }}<",
    ">上传音频并转写<": ">{{ $t('transcript.uploadAndTranscribe') }}<",
    ">开始录音<": ">{{ $t('transcript.startRecord') }}<",
    ">暂停录音<": ">{{ $t('transcript.pauseRecord') }}<",
    ">继续录音<": ">{{ $t('transcript.resumeRecord') }}<",
    ">停止并转写<": ">{{ $t('transcript.stopAndTranscribe') }}<",
    ">生成纪要与任务<": ">{{ $t('transcript.generateSummary') }}<",
    ">导出纪要<": ">{{ $t('transcript.exportSummary') }}<",
    ">复制摘要<": ">{{ $t('transcript.copySummary') }}<",
    "录音状态：": "{{ $t('transcript.recordingStatus') }}：",

    # Tasks
    "label=\"任务标题\"": ":label=\"$t('task.taskTitle')\"",
    "label=\"优先级\"": ":label=\"$t('task.priority')\"",
    "label=\"截止日期\"": ":label=\"$t('task.dueDate')\"",
    ">任务中心<": ">{{ $t('task.title') }}<",
    ">集中查看全部会议行动项，并支持手动调整负责人与优先级。<": ">{{ $t('task.description') }}<",
    ">应用筛选<": ">{{ $t('task.applyFilters') }}<",
    ">AI行动项：由转写自动识别<": ">{{ $t('task.tagAI') }}<",
    ">手动任务：会议中人工创建<": ">{{ $t('task.tagManual') }}<",
    ">逾期：已超过截止时间<": ">{{ $t('task.tagOverdue') }}<",
    "label=\"任务分类\"": ":label=\"$t('task.category')\"",
    "\"AI行动项\"": "t('task.typeAI')",
    "\"手动任务\"": "t('task.typeManual')",
    ">逾期<": ">{{ $t('task.overdue') }}<",
    ">即将到期<": ">{{ $t('task.dueSoon') }}<",
    ">高优先级<": ">{{ $t('task.highPriority') }}<",
    ">未分配<": ">{{ $t('task.unassigned') }}<",
    "label=\"负责人\"": ":label=\"$t('task.assignee')\"",
    ">编辑任务<": ">{{ $t('task.editTask') }}<",
    "label=\"标题\"": ":label=\"$t('task.taskTitle')\"",
    "placeholder=\"请输入任务标题\"": ":placeholder=\"$t('task.taskTitlePlaceholder')\"",
    "placeholder=\"可选\"": ":placeholder=\"$t('task.taskDescriptionPlaceholder')\"",
    "placeholder=\"请选择负责人\"": ":placeholder=\"$t('task.selectAssignee')\"",
    "\"加载用户失败\"": "t('task.loadUserFailed')",
    "\"任务标题不能为空\"": "t('task.titleRequired')",
    "\"任务已更新\"": "t('task.updateSuccess')",
    "\"更新任务失败\"": "t('task.updateFailed')",
    "\"用户 #\"": "t('task.userPrefix')",
    ">任务列表<": ">{{ $t('task.listTitle') }}<",
    "description=\"暂无任务\"": ":description=\"$t('task.empty')\"",
    "label=\"待办\"": ":label=\"$t('task.statusTodo')\"",
    "label=\"进行中\"": ":label=\"$t('task.statusInProgress')\"",
    "label=\"已完成\"": ":label=\"$t('task.statusDone')\"",
    "\"当前页面仅支持任务状态管理，请前往任务中心创建任务\"": "t('task.statusManageOnly')",
    "\"状态已更新\"": "t('task.statusUpdateSuccess')",
    "\"高\"": "t('task.priorityHigh')",
    "\"中\"": "t('task.priorityMedium')",
    "\"低\"": "t('task.priorityLow')",

    # Participants
    ">参与者<": ">{{ $t('participant.title') }}<",
    "placeholder=\"选择用户\"": ":placeholder=\"$t('participant.selectUser')\"",
    "label=\"必须\"": ":label=\"$t('participant.roleRequired')\"",
    "label=\"可选\"": ":label=\"$t('participant.roleOptional')\"",
    "label=\"旁听\"": ":label=\"$t('participant.roleObserver')\"",
    "description=\"暂无参与者\"": ":description=\"$t('participant.empty')\"",
    ">无邮箱<": ">{{ $t('participant.noEmail') }}<",
    "title=\"确认移除该参与者？\"": ":title=\"$t('participant.removeConfirm')\"",
    "\"请先选择用户\"": "t('participant.selectUserFirst')",
    "\"参与者已添加\"": "t('participant.addSuccess')",
    "\"参与者角色已更新\"": "t('participant.roleUpdateSuccess')",
    "\"参与者已移除\"": "t('participant.removeSuccess')",
    "\"待确认\"": "t('participant.statusInvited')",
    "\"已接受\"": "t('participant.statusAccepted')",
    "\"已拒绝\"": "t('participant.statusDeclined')",
    "\"已参加\"": "t('participant.statusAttended')",

    # Stats
    "title=\"转写片段\"": ":title=\"$t('stats.transcriptCount')\"",
    "title=\"任务数\"": ":title=\"$t('stats.taskCount')\"",
    "title=\"已完成任务\"": ":title=\"$t('stats.doneTaskCount')\"",

    # Error
    ">重试<": ">{{ $t('error.retry') }}<",
    ">返回上一页<": ">{{ $t('error.back') }}<",
    "title=\"错误详情\"": ":title=\"$t('error.details')\"",
    "\"页面出现错误\"": "t('error.pageError')",
    "\"GPU 显存不足\"": "t('error.gpuOOM')",
    "\"GPU 不可用\"": "t('error.gpuUnavailable')",
    "\"GPU 处理失败\"": "t('error.gpuFailed')",
    "\"模型加载超时\"": "t('error.modelTimeout')",
    "\"模型加载失败\"": "t('error.modelFailed')",
    "\"音频转写失败\"": "t('error.transcribeFailed')",
    "\"转写处理超时\"": "t('error.transcribeTimeout')",
    "\"音频处理失败\"": "t('error.audioFailed')",
    "\"音频格式不支持\"": "t('error.invalidAudio')",
    "\"说话人识别失败\"": "t('error.diarizationFailed')",
    "\"AI 服务不可用\"": "t('error.aiUnavailable')",
    "\"网络连接超时\"": "t('error.networkTimeout')",
    "\"网络连接失败\"": "t('error.networkError')",
    "\"请稍后重试或联系管理员\"": "t('error.defaultMessage')",
    "建议：": "{{ $t('error.suggestionPrefix') }}",

    # AudioFiles
    ">文件名<": ">{{ $t('audio.filename') }}<",
    ">大小<": ">{{ $t('audio.size') }}<",
    ">上传时间<": ">{{ $t('audio.uploadedAt') }}<",
    ">播放<": ">{{ $t('audio.play') }}<",
    ">下载<": ">{{ $t('audio.download') }}<",
    "\"加载录音列表失败\"": "t('audio.loadFailed')",
    "\"音频加载失败，请检查文件是否存在\"": "t('audio.loadAudioFailed')",
    "description=\"暂无录音文件\"": ":description=\"$t('audio.empty')\"",

    # Summary
    ">议程<": ">{{ $t('summary.agenda') }}<",
    ">决议<": ">{{ $t('summary.resolutions') }}<",
    ">提议人:<": ">{{ $t('summary.proposer') }}<",
    ">待办事项<": ">{{ $t('summary.todos') }}<",
    "title=\"原始摘要\"": ":title=\"$t('summary.rawSummary')\"",
    "\"暂无会议摘要\"": "t('summary.emptySummary')",
    "\"折叠摘要\"": "t('summary.collapse')",
    "\"展开全文\"": "t('summary.expand')"
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    script_changed = False

    for k, v in replacements.items():
        if k in content:
            content = content.replace(k, v)
            if v.startswith("t('") or v.startswith("$t("):
                script_changed = True

    if script_changed:
        # Check if useI18n needs to be added
        if 'useI18n' not in content and 't(' in content and ('<script setup' in content or '<script lang="ts" setup>' in content):
            content = re.sub(r'(<script setup.*?>\n)', r'\1import { useI18n } from "vue-i18n";\n', content, count=1)
            # Find the first const or function and inject `const { t } = useI18n();` before it
            if 'const ' in content:
                content = content.replace('const ', 'const { t } = useI18n();\nconst ', 1)
            elif 'function ' in content:
                content = content.replace('function ', 'const { t } = useI18n();\nfunction ', 1)
            else:
                content = content.replace('import { useI18n } from "vue-i18n";\n', 'import { useI18n } from "vue-i18n";\n\nconst { t } = useI18n();\n', 1)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(VUE_FILES_DIR):
    for file in files:
        if file.endswith('.vue') or file.endswith('.ts'):
            process_file(os.path.join(root, file))

print("Replacement done")