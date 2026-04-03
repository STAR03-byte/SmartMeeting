<template>
  <div v-if="hasError" class="error-boundary">
    <el-result
      :icon="errorIcon"
      :title="errorTitle"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="handleRetry">
          {{ $t('error.retry') }}
        </el-button>
        <el-button @click="handleGoBack">
          {{ $t('error.back') }}
        </el-button>
      </template>
    </el-result>
    <div v-if="showDetails" class="error-details">
      <el-collapse>
        <el-collapse-item :title="$t('error.details')" name="details">
          <pre>{{ errorDetails }}</pre>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
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
  if (!code) return t('error.pageError');

  const titleMap: Record<string, string> = {
    GPU_OUT_OF_MEMORY: t('error.gpuOOM'),
    GPU_NOT_AVAILABLE: t('error.gpuUnavailable'),
    GPU_PROCESSING_FAILED: t('error.gpuFailed'),
    MODEL_LOADING_TIMEOUT: t('error.modelTimeout'),
    MODEL_LOADING_FAILED: t('error.modelFailed'),
    TRANSCRIPTION_FAILED: t('error.transcribeFailed'),
    TRANSCRIPTION_TIMEOUT: t('error.transcribeTimeout'),
    AUDIO_PROCESSING_FAILED: t('error.audioFailed'),
    INVALID_AUDIO_FORMAT: t('error.invalidAudio'),
    SPEAKER_DIARIZATION_FAILED: t('error.diarizationFailed'),
    AI_SERVICE_UNAVAILABLE: t('error.aiUnavailable'),
    NETWORK_TIMEOUT: t('error.networkTimeout'),
    NETWORK_ERROR: t('error.networkError'),
  };

  return titleMap[code] || t('error.pageError');
});

const errorMessage = computed(() => {
  if (!errorInfo.value) return t('error.defaultMessage');

  let message = errorInfo.value.message || t('error.defaultMessage');

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