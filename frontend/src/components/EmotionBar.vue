<template>
  <div class="emotion-bar">
    <div class="bar-track">
      <div class="bar-fill" :style="barStyle"></div>
      <div class="bar-center"></div>
    </div>
    <span class="val" :style="{ color: valColor }">{{ displayVal }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ value: { type: Number, default: 0 } })

const barStyle = computed(() => {
  const v = props.value || 0
  if (v >= 0) {
    return { left: '50%', width: `${v * 50}%`, background: 'var(--green)' }
  } else {
    return { right: '50%', width: `${Math.abs(v) * 50}%`, background: 'var(--red)' }
  }
})

const valColor = computed(() => {
  const v = props.value || 0
  if (v > 0.2) return 'var(--green)'
  if (v < -0.2) return 'var(--red)'
  return 'var(--text-dim)'
})

const displayVal = computed(() => (props.value || 0).toFixed(2))
</script>

<style scoped>
.emotion-bar { display: flex; align-items: center; gap: 6px; flex: 1; }
.bar-track {
  flex: 1;
  height: 6px;
  background: var(--bg-4);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}
.bar-fill { position: absolute; height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.bar-center {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border-bright);
}
.val { font-size: 11px; min-width: 36px; text-align: right; }
</style>
