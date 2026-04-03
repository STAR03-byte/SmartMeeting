<template>
  <el-drawer
    v-bind="$attrs"
    :header-class="['wb-drawer-header', headerClass].join(' ')"
    :body-class="['wb-drawer-body', bodyClass].join(' ')"
    :footer-class="['wb-drawer-footer', footerClass].join(' ')"
  >
    <template v-for="(_, name) in $slots" #[name]="slotData">
      <slot :name="name" v-bind="slotData || {}"></slot>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
defineOptions({
  inheritAttrs: false
})

withDefaults(defineProps<{
  headerClass?: string
  bodyClass?: string
  footerClass?: string
}>(), {
  headerClass: '',
  bodyClass: '',
  footerClass: ''
})
</script>
