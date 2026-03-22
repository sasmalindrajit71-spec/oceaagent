<template>
  <div class="political-lean">
    <div class="lean-track">
      <div class="lean-fill" :style="fillStyle"></div>
      <div class="lean-center"></div>
    </div>
    <span class="lean-val" :style="{ color: valColor }">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ value: { type: Number, default: 0 } })

const fillStyle = computed(() => {
  const v = props.value || 0
  if (v >= 0) {
    return { left: '50%', width: `${v * 50}%`, background: 'var(--red)' }
  } else {
    return { right: '50%', width: `${Math.abs(v) * 50}%`, background: 'var(--accent)' }
  }
})

const valColor = computed(() => {
  const v = props.value || 0
  if (v > 0.3) return 'var(--red)'
  if (v < -0.3) return 'var(--accent)'
  return 'var(--text-dim)'
})

const label = computed(() => {
  const v = props.value || 0
  if (v > 0.6) return 'Far Right'
  if (v > 0.2) return 'Right'
  if (v < -0.6) return 'Far Left'
  if (v < -0.2) return 'Left'
  return 'Center'
})
</script>

<style scoped>
.political-lean { display: flex; align-items: center; gap: 6px; flex: 1; }
.lean-track {
  flex: 1;
  height: 6px;
  background: var(--bg-4);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}
.lean-fill { position: absolute; height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.lean-center {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border-bright);
}
.lean-val { font-size: 10px; min-width: 52px; text-align: right; }
</style>
