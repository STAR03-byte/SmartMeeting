import os
import re
import json

files = [
    'frontend/src/App.vue',
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

chinese_pattern = re.compile(r'[\u4e00-\u9fa5]+')
results = []

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                matches = chinese_pattern.findall(line)
                if matches:
                    results.append({"file": f, "line_no": i+1, "line": line.strip(), "matches": matches})

with open("i18n_strings.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Done")