import os
import re

translations = {
  '确认': 'common.confirm',
  '取消': 'common.cancel',
  '保存': 'common.save',
  '删除': 'common.delete',
  '编辑': 'common.edit',
  '创建': 'common.create',
  '添加': 'common.add',
  '刷新': 'common.refresh',
  '返回': 'common.back',
  '操作': 'common.operations',
  '状态': 'common.status',
  '关闭': 'common.close',
  '查看': 'common.view',
  '描述': 'common.description',
  '未知': 'common.unknown',
  '已登录': 'common.loggedIn',
  '退出登录': 'common.logout',
  '去登录': 'common.goToLogin',
  '仪表盘': 'app.navDashboard',
  '会议列表': 'app.navMeetings',
  '任务中心': 'app.navTasks',
  '热词设置': 'app.navHotwords',
  '新建会议': 'dashboard.newMeeting',
  '早上好': 'dashboard.morning',
  '下午好': 'dashboard.afternoon',
  '晚上好': 'dashboard.evening',
  '高效会议管理，智能任务追踪': 'dashboard.slogan',
  '会议总数': 'dashboard.totalMeetings',
  '近期会议': 'dashboard.recentMeetings',
  '查看全部': 'dashboard.viewAll',
  '暂无会议数据': 'dashboard.noMeetingData',
  '快捷操作': 'dashboard.quickActions',
  '任务管理': 'dashboard.taskManagement',
  '用户管理': 'dashboard.userManagement',
  '我的团队': 'team.title',
  '创建团队': 'team.createTeam',
  '团队名称': 'team.teamName',
  '我的角色': 'team.myRole',
  '加载团队列表失败': 'team.loadFailed',
  '所有者': 'team.roleOwner',
  '管理员': 'team.roleAdmin',
  '成员': 'team.roleMember',
  '团队详情': 'team.detailTitle',
  '基本信息': 'team.basicInfo',
  '暂无描述': 'team.noDescription',
  '创建时间': 'team.createdAt',
  '成员管理': 'team.memberManagement',
  '添加成员': 'team.addMember',
  '姓名': 'team.memberName',
  '邮箱': 'team.email',
  '角色': 'team.role',
  '加入时间': 'team.joinedAt',
  '确定要移除该成员吗？': 'team.removeConfirm',
  '移除': 'team.remove',
  '选择用户': 'team.selectUser',
  '请选择用户': 'team.selectUserRequired',
  '请选择要添加的用户': 'team.selectUserPlaceholder',
  '请选择角色': 'team.roleRequired',
  '确认添加': 'team.confirmAdd',
  '加载团队信息失败': 'team.loadTeamFailed',
  '加载成员列表失败': 'team.loadMemberFailed',
  '加载用户列表失败': 'team.loadUserFailed',
  '添加成员成功': 'team.addMemberSuccess',
  '添加成员失败': 'team.addMemberFailed',
  '成员已移除': 'team.memberRemoved',
  '移除成员失败': 'team.removeMemberFailed',
  '角色更新成功': 'team.roleUpdateSuccess',
  '角色更新失败': 'team.roleUpdateFailed',
  '请输入团队名称': 'team.teamNameRequired',
  '长度在 2 到 50 个字符': 'team.teamNameLength',
  '请输入团队描述（可选）': 'team.teamDescriptionPlaceholder',
  '团队创建成功': 'team.createSuccess',
  '确认删除此会议？': 'meeting.deleteConfirm',
  '会议工作台': 'meeting.workbench',
  '组织者': 'meeting.organizer',
  '计划中': 'meeting.statusPlanned',
  '进行中': 'meeting.statusOngoing',
  '已结束': 'meeting.statusDone',
  '已取消': 'meeting.statusCancelled',
  '生成分享链接': 'meeting.generateShareLink',
  '邮件分发': 'meeting.emailDistribute',
  '新建任务': 'meeting.newTask',
  '会议ID无效': 'meeting.invalidMeetingId',
  '分享链接已生成并复制': 'meeting.shareLinkGenerated',
  '分享链接已复制': 'meeting.shareLinkCopied',
  '会议纪要': 'meeting.meetingSummary',
  '已打开邮件客户端': 'meeting.emailClientOpened',
  '会议标题': 'meeting.title',
  '会议描述': 'meeting.description',
  '开始时间': 'meeting.startTime',
  '结束时间': 'meeting.endTime',
  '热词管理': 'hotword.title',
  '维护个人热词，提升 Whisper 转写准确率。': 'hotword.description',
  '新增热词': 'hotword.addHotword',
  '热词': 'hotword.hotword',
  '输入热词，例如项目名、人名': 'hotword.hotwordPlaceholder',
  '添加热词': 'hotword.add',
  '热词列表': 'hotword.list',
  '确认删除此热词？': 'hotword.deleteConfirm',
  '加载热词失败': 'hotword.loadFailed',
  '请输入热词': 'hotword.inputRequired',
  '热词已添加': 'hotword.addSuccess',
  '已删除': 'hotword.deleteSuccess',
  '转写片段': 'transcript.title',
  '暂无转写内容': 'transcript.empty',
  '确认删除该转写片段？': 'transcript.deleteConfirm',
  '录音文件': 'transcript.audioRecordTitle',
  '上传音频并转写': 'transcript.uploadAndTranscribe',
  '开始录音': 'transcript.startRecord',
  '暂停录音': 'transcript.pauseRecord',
  '继续录音': 'transcript.resumeRecord',
  '停止并转写': 'transcript.stopAndTranscribe',
  '生成纪要与任务': 'transcript.generateSummary',
  '导出纪要': 'transcript.exportSummary',
  '复制摘要': 'transcript.copySummary',
  '录音状态': 'transcript.recordingStatus',
  '任务中心': 'task.title',
  '集中查看全部会议行动项，并支持手动调整负责人与优先级。': 'task.description',
  '应用筛选': 'task.applyFilters',
  'AI行动项：由转写自动识别': 'task.tagAI',
  '手动任务：会议中人工创建': 'task.tagManual',
  '逾期：已超过截止时间': 'task.tagOverdue',
  '优先级': 'task.priority',
  '任务分类': 'task.category',
  'AI行动项': 'task.typeAI',
  '手动任务': 'task.typeManual',
  '逾期': 'task.overdue',
  '即将到期': 'task.dueSoon',
  '高优先级': 'task.highPriority',
  '未分配': 'task.unassigned',
  '负责人': 'task.assignee',
  '编辑任务': 'task.editTask',
  '标题': 'task.taskTitle',
  '请输入任务标题': 'task.taskTitlePlaceholder',
  '描述': 'task.taskDescription',
  '可选': 'task.taskDescriptionPlaceholder',
  '请选择负责人': 'task.selectAssignee',
  '加载用户失败': 'task.loadUserFailed',
  '任务标题不能为空': 'task.titleRequired',
  '任务已更新': 'task.updateSuccess',
  '更新任务失败': 'task.updateFailed',
  '用户 #': 'task.userPrefix',
  '任务列表': 'task.listTitle',
  '暂无任务': 'task.empty',
  '待办': 'task.statusTodo',
  '进行中': 'task.statusInProgress',
  '已完成': 'task.statusDone',
  '当前页面仅支持任务状态管理，请前往任务中心创建任务': 'task.statusManageOnly',
  '状态已更新': 'task.statusUpdateSuccess',
  '高': 'task.priorityHigh',
  '中': 'task.priorityMedium',
  '低': 'task.priorityLow',
  '参与者': 'participant.title',
  '选择用户': 'participant.selectUser',
  '必须': 'participant.roleRequired',
  '可选': 'participant.roleOptional',
  '旁听': 'participant.roleObserver',
  '暂无参与者': 'participant.empty',
  '无邮箱': 'participant.noEmail',
  '确认移除该参与者？': 'participant.removeConfirm',
  '请先选择用户': 'participant.selectUserFirst',
  '参与者已添加': 'participant.addSuccess',
  '参与者角色已更新': 'participant.roleUpdateSuccess',
  '参与者已移除': 'participant.removeSuccess',
  '待确认': 'participant.statusInvited',
  '已接受': 'participant.statusAccepted',
  '已拒绝': 'participant.statusDeclined',
  '已参加': 'participant.statusAttended',
  '转写片段': 'stats.transcriptCount',
  '任务数': 'stats.taskCount',
  '已完成任务': 'stats.doneTaskCount',
  '重试': 'error.retry',
  '返回上一页': 'error.back',
  '错误详情': 'error.details',
  '页面出现错误': 'error.pageError',
  'GPU 显存不足': 'error.gpuOOM',
  'GPU 不可用': 'error.gpuUnavailable',
  'GPU 处理失败': 'error.gpuFailed',
  '模型加载超时': 'error.modelTimeout',
  '模型加载失败': 'error.modelFailed',
  '音频转写失败': 'error.transcribeFailed',
  '转写处理超时': 'error.transcribeTimeout',
  '音频处理失败': 'error.audioFailed',
  '音频格式不支持': 'error.invalidAudio',
  '说话人识别失败': 'error.diarizationFailed',
  'AI 服务不可用': 'error.aiUnavailable',
  '网络连接超时': 'error.networkTimeout',
  '网络连接失败': 'error.networkError',
  '请稍后重试或联系管理员': 'error.defaultMessage',
  '建议：': 'error.suggestionPrefix',
  '录音文件': 'audio.title',
  '暂无录音文件': 'audio.empty',
  '文件名': 'audio.filename',
  '大小': 'audio.size',
  '上传时间': 'audio.uploadedAt',
  '播放': 'audio.play',
  '下载': 'audio.download',
  '加载录音列表失败': 'audio.loadFailed',
  '音频加载失败，请检查文件是否存在': 'audio.loadAudioFailed',
  '议程': 'summary.agenda',
  '决议': 'summary.resolutions',
  '提议人:': 'summary.proposer',
  '待办事项': 'summary.todos',
  '原始摘要': 'summary.rawSummary',
  '暂无会议摘要': 'summary.emptySummary',
  '折叠摘要': 'summary.collapse',
  '展开全文': 'summary.expand',
  '所有会议': 'common.all',
  '全部': 'common.all',
  '搜索': 'common.search',
  '筛选': 'common.filter',
  '重置': 'common.reset',
  '关键词': 'common.keyword',
  '所属会议': 'task.meeting',
  '提醒': 'task.reminder',
  '搜索标题/描述': 'common.searchPlaceholder',
  '搜索任务标题': 'task.searchPlaceholder',
  '排序': 'common.sort',
  '按创建时间（新→旧）': 'task.sortCreatedDesc',
  '按截止时间（近→远）': 'task.sortDueAsc',
  '按截止时间（远→近）': 'task.sortDueDesc',
  '会议管理': 'app.navMeetings',
  '会议地点（可选）': 'meeting.locationOptional',
  '会议': 'meeting.title',
  '地点': 'meeting.location',
  '已逾期': 'task.overdue',
  '暂无可选组织者，请先创建用户': 'meeting.noOrganizer',
  '获取团队列表失败': 'team.loadFailed',
  '添加参与者失败': 'participant.addFailed',
  '会议创建成功': 'meeting.createSuccess',
  '创建失败': 'meeting.createFailed',
  '会议已删除': 'meeting.deleteSuccess',
  '删除失败': 'meeting.deleteFailed',
  '选择开始时间': 'meeting.selectStartTime',
  '选择结束时间': 'meeting.selectEndTime',
  '选择团队（可选）': 'team.selectTeamOptional',
  '选择团队': 'team.selectTeam',
  '请输入会议标题': 'meeting.titlePlaceholder',
  '请输入会议描述（可选）': 'meeting.descriptionPlaceholder',
  '选择参与人员（可选）': 'participant.selectParticipantOptional',
  '所属团队': 'meeting.team',
  '上传失败': 'common.uploadFailed',
  '转写成功': 'transcript.success'
}

files = [
    'frontend/src/views/TeamsView.vue',
    'frontend/src/views/TeamDetailView.vue',
    'frontend/src/components/MeetingCard.vue',
    'frontend/src/views/TeamCreateView.vue',
    'frontend/src/views/DashboardView.vue',
    'frontend/src/views/TasksView.vue',
    'frontend/src/components/ErrorBoundary.vue',
    'frontend/src/views/SharedMeetingView.vue',
    'frontend/src/components/meeting/TranscriptPanel.vue',
    'frontend/src/components/meeting/StatsOverview.vue',
    'frontend/src/views/MeetingListView.vue',
    'frontend/src/components/meeting/TaskManager.vue',
    'frontend/src/components/meeting/ParticipantManager.vue',
    'frontend/src/views/MeetingDetailView.vue',
    'frontend/src/views/LoginView.vue',
    'frontend/src/components/meeting/SummaryPanel.vue',
    'frontend/src/components/meeting/AudioRecorder.vue',
    'frontend/src/views/HotwordsView.vue',
    'frontend/src/components/meeting/AudioFiles.vue'
]

def replace_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    
    for zh, key in sorted(translations.items(), key=lambda x: len(x[0]), reverse=True):
        # 1. Replace in template text nodes: >中文< -> >{{ $t('key') }}<
        # We need to handle cases where there is whitespace around the Chinese text
        # A simple replacement for `>Text<` isn't enough, we must match `Text` as long as it's outside tags or inside {{ }}? No, just replacing the exact string `Text` when it's not inside an attribute.
        
        # 2. Replace in attributes: attr="中文" -> :attr="$t('key')"
        # Regex to find attr="some_text_with_zh"
        
        # To be very safe, let's just do plain text replacements.
        # But replacing "确认" everywhere might break things if it's part of a variable name (unlikely for Chinese).
        pass

    # A much safer AST approach for Vue isn't trivial in Python.
    # Let's just write a very specific regex replacement engine for Vue strings.

    # 1. Attribute replacement: label="中文" -> :label="$t('key')"
    for attr in ["label", "placeholder", "title", "description", "content", "effect"]:
        for zh, key in translations.items():
            content = content.replace(f' {attr}="{zh}"', f' :{attr}="$t(\'{key}\')"')
            content = content.replace(f' {attr}="{zh}（可选）"', f' :{attr}="$t(\'{key}\')"')
    
    # 2. Template text replacement: <tag>中文</tag> -> <tag>{{ $t('key') }}</tag>
    for zh, key in translations.items():
        # Match > spaces zh spaces <
        content = re.sub(f'>(\\s*){zh}(\\s*)<', f'>\\1{{{{ $t(\'{key}\') }}}}\\2<', content)
        
    # 3. Inside existing interpolations: {{ "中文" }} -> {{ $t('key') }}
    for zh, key in translations.items():
        content = content.replace(f'"{zh}"', f'$t(\'{key}\')')
        content = content.replace(f"'{zh}'", f"$t('{key}')")
        content = content.replace(f'`{zh}`', f"$t('{key}')")

    if content != original_content:
        # Check if useI18n is imported
        if "<script setup" in content and "useI18n" not in content:
            script_tag = re.search(r'<script setup.*?>', content)
            if script_tag:
                content = content.replace(
                    script_tag.group(0),
                    script_tag.group(0) + "\nimport { useI18n } from 'vue-i18n';\nconst { t } = useI18n();"
                )
        
        # Replace $t inside script setup with t
        # (This is tricky because we replaced "中文" with $t('key'), but in script it should be t('key'))
        # Let's extract script block and fix it.
        script_match = re.search(r'(<script.*?>)(.*?)(</script>)', content, re.DOTALL)
        if script_match:
            script_content = script_match.group(2)
            script_content = script_content.replace("$t(", "t(")
            content = content[:script_match.start(2)] + script_content + content[script_match.end(2):]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

for f in files:
    if os.path.exists(f):
        replace_in_file(f)

print("Done replacing.")