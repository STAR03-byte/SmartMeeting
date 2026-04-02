import { computed } from "vue";
import { ElMessage } from "element-plus";
import { useMeetingStore } from "../stores/meetingStore";
import type { Speaker, DiarizationSegment } from "../api/types";

/**
 * 说话人分离功能 Composable
 * 提供说话人管理、重命名等功能
 */
export function useSpeakerDiarization(meetingId: number) {
  const store = useMeetingStore();

  const speakers = computed(() => {
    const speakerMap = new Map<string, Speaker>();
    
    store.transcripts.forEach((transcript) => {
      if (!transcript.speaker_name) return;
      
      const speakerId = transcript.speaker_user_id?.toString() || `speaker-${transcript.segment_index}`;
      
      if (!speakerMap.has(speakerId)) {
        speakerMap.set(speakerId, {
          id: speakerId,
          name: transcript.speaker_name,
          color: getSpeakerColor(speakerId),
          segment_count: 0,
          total_duration_sec: 0,
        });
      }
      
      const speaker = speakerMap.get(speakerId)!;
      speaker.segment_count += 1;
      
      if (transcript.start_time_sec !== null && transcript.end_time_sec !== null) {
        speaker.total_duration_sec += transcript.end_time_sec - transcript.start_time_sec;
      }
    });
    
    return Array.from(speakerMap.values());
  });

  const diarizationSegments = computed<DiarizationSegment[]>(() => {
    return store.transcripts
      .filter((t) => t.speaker_name !== null)
      .map((transcript) => ({
        speaker_id: transcript.speaker_user_id?.toString() || `speaker-${transcript.segment_index}`,
        speaker_name: transcript.speaker_name || "未知说话人",
        start_time_sec: transcript.start_time_sec || 0,
        end_time_sec: transcript.end_time_sec || 0,
        content: transcript.content,
      }));
  });

  const hasDiarization = computed(() => {
    return store.transcripts.some((t) => t.speaker_name !== null);
  });

  /**
   * 重命名说话人
   * @param speakerId 说话人ID
   * @param newName 新名称
   */
  async function renameSpeaker(speakerId: string, newName: string): Promise<void> {
    try {
      // TODO: 调用后端 API 更新说话人名称
      store.updateSpeakerName(speakerId, newName);
      
      ElMessage.success(`已将说话人重命名为 "${newName}"`);
    } catch (error) {
      ElMessage.error(`重命名失败：${getErrorMessage(error)}`);
      throw error;
    }
  }

  /**
   * 获取说话人颜色
   * 基于说话人ID生成固定颜色
   */
  function getSpeakerColor(speakerId: string): string {
    const colors = [
      "#409EFF", // 蓝色
      "#67C23A", // 绿色
      "#E6A23C", // 橙色
      "#F56C6C", // 红色
      "#909399", // 灰色
      "#9C27B0", // 紫色
      "#00BCD4", // 青色
      "#FF9800", // 深橙色
    ];
    
    // 使用说话人ID的哈希值选择颜色
    let hash = 0;
    for (let i = 0; i < speakerId.length; i++) {
      hash = speakerId.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    return colors[Math.abs(hash) % colors.length];
  }

  /**
   * 格式化说话人时长
   * @param seconds 秒数
   */
  function formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    
    if (minutes === 0) {
      return `${secs}秒`;
    }
    
    return `${minutes}分${secs}秒`;
  }

  /**
   * 清除说话人分离数据
   */
  function clearDiarization(): void {
    store.clearDiarizationData();
  }

  return {
    speakers,
    diarizationSegments,
    hasDiarization,
    renameSpeaker,
    getSpeakerColor,
    formatDuration,
    clearDiarization,
  };
}

/**
 * 获取错误消息
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}