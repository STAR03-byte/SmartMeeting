<template>
  <el-alert
    v-if="error"
    :title="error"
    type="error"
    show-icon
    :closable="closable"
    @close="emit('close')"
  />
</template>

<script setup lang="ts">
const emit = defineEmits<{
  close: [];
}>();

withDefaults(
  defineProps<{
    error: string | null;
    closable?: boolean;
  }>(),
  {
    closable: true,
  },
);
</script>
