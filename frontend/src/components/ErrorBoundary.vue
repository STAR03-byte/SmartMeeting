<template>
  <div v-if="hasError" class="error-boundary">
    <el-result
      :icon="errorIcon"
      :title="errorTitle"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="handleRetry">
          重试
        </el-button>
        <el-button @click="handleGoBack">
          返回上一页
        </el-button>
      </template>
    </el-result>
    <div v-if="showDetails" class="error-details">
      <el-collapse>
        <el-collapse-item title="错误详情" name="details">
          <pre>{{ errorDetails }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, computed, onErrorCaptured, type ComponentPublicInstance } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

interface ErrorInfo {
  message: string;
  code?: string;
  suggestion?: string;
  details?: Record<string, unknown>;
}

const props = withDefaults(
  defineProps<{
    showDetails?: boolean;
    onError?: (error: Error, instance: ComponentPublicInstance | null, info: string) => void;
  }>(),
  {
    showDetails: false,
  }
);

const router = useRouter();
const hasError = ref(false);
const error = ref<Error | null>(null);
const errorInfo = ref<ErrorInfo | null>(null);

const errorIcon = computed(() => {
  const code = errorInfo.value?.code;
  if (!code) return "error";

  if (code.includes("GPU") || code.includes("MODEL")) {
    return "warning";
  }
  if (code.includes("NETWORK") || code.includes("TIMEOUT")) {
    return "warning";
  }
  if (code.includes("TRANSCRIPTION") || code.includes("AUDIO")) {
    return "warning";
  }
  return "error";
});

const errorTitle = computed(() => {
  const code = errorInfo.value?.code;
  if (!code) return "页面出现错误";

  const titleMap: Record<string, string> = {
    GPU_OUT_OF_MEMORY: "GPU 显存不足",
    GPU_NOT_AVAILABLE: "GPU 不可用",
    GPU_PROCESSING_FAILED: "GPU 处理失败",
    MODEL_LOADING_TIMEOUT: "模型加载超时",
    MODEL_LOADING_FAILED: "模型加载失败",
    TRANSCRIPTION_FAILED: "音频转写失败",
    TRANSCRIPTION_TIMEOUT: "转写处理超时",
    AUDIO_PROCESSING_FAILED: "音频处理失败",
    INVALID_AUDIO_FORMAT: "音频格式不支持",
    SPEAKER_DIARIZATION_FAILED: "说话人识别失败",
    AI_SERVICE_UNAVAILABLE: "AI 服务不可用",
    NETWORK_TIMEOUT: "网络连接超时",
    NETWORK_ERROR: "网络连接失败",
  };

  return titleMap[code] || "页面出现错误";
});

const errorMessage = computed(() => {
  if (!errorInfo.value) return "请稍后重试或联系管理员";

  let message = errorInfo.value.message || "请稍后重试或联系管理员";

  if (errorInfo.value.suggestion) {
    message += `\n\n建议：${errorInfo.value.suggestion}`;
  }

  return message;
});

const errorDetails = computed(() => {
  if (!error.value) return "";
  return JSON.stringify(
    {
      name: error.value.name,
      message: error.value.message,
      stack: error.value.stack,
      info: errorInfo.value,
    },
    null,
    2
  );
});

onErrorCaptured((err: Error, instance: ComponentPublicInstance | null, info: string) => {
  hasError.value = true;
  error.value = err;

  const axiosError = err as { response?: { data?: { error_code?: string; detail?: string; suggestion?: string } } };
  if (axiosError.response?.data) {
    errorInfo.value = {
      message: axiosError.response.data.detail || err.message,
      code: axiosError.response.data.error_code,
      suggestion: axiosError.response.data.suggestion,
    };
  } else {
    errorInfo.value = {
      message: err.message,
    };
  }

  if (props.onError) {
    props.onError(err, instance, info);
  }

  ElMessage.error({
    message: errorTitle.value,
    duration: 5000,
  });

  return false;
});

const handleRetry = () => {
  hasError.value = false;
  error.value = null;
  errorInfo.value = null;
};

const handleGoBack = () => {
  router.back();
};
</script>

<style scoped>
.error-boundary {
  padding: 20px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.error-details {
  margin-top: 20px;
  max-width: 800px;
  width: 100%;
}

.error-details pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>