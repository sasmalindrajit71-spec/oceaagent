<template>
  <div class="inspector">
    <div class="inspector-header">
      <div class="inspector-title">
        <span :class="`tag tag-${agent.tier === 'deep' ? 'completed' : 'pending'}`">{{ agent.tier }}</span>
        <h2>{{ agent.name }}</h2>
      </div>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>

    <div class="inspector-body">
      <!-- Identity -->
      <div class="section">
        <div class="section-title">Identity</div>
        <div class="meta-grid">
          <div class="meta-item"><span class="dim">Age</span><span>{{ agent.age }}</span></div>
          <div class="meta-item"><span class="dim">Occupation</span><span>{{ agent.occupation }}</span></div>
          <div class="meta-item"><span class="dim">Education</span><span>{{ agent.education }}</span></div>
          <div class="meta-item"><span class="dim">Location</span><span>{{ agent.location }}</span></div>
          <div class="meta-item"><span class="dim">Cluster</span><span>#{{ agent.cluster_id }}</span></div>
          <div class="meta-item"><span class="dim">Influence</span><span class="accent">{{ agent.influence_score?.toFixed(3) }}</span></div>
        </div>
      </div>

      <!-- LLM Assignment -->
      <div class="section">
        <div class="section-title">LLM Assignment</div>
        <div class="meta-grid">
          <div class="meta-item"><span class="dim">Provider</span><span class="accent">{{ agent.provider }}</span></div>
          <div class="meta-item full"><span class="dim">Model</span><span>{{ agent.model }}</span></div>
        </div>
      </div>

      <!-- Emotional State -->
      <div class="section">
        <div class="section-title">Emotional State</div>
        <div class="emotion-row">
          <span class="dim">Baseline</span>
          <EmotionBar :value="agent.emotional_baseline" />
        </div>
        <div class="emotion-row">
          <span class="dim">Current</span>
          <EmotionBar :value="agent.current_emotion" />
        </div>
        <div class="emotion-row">
          <span class="dim">Political</span>
          <PoliticalLean :value="agent.political_lean" />
        </div>
      </div>

      <!-- Big Five Personality -->
      <div class="section">
        <div class="section-title">Big Five Personality</div>
        <div class="trait-list">
          <div v-for="trait in BIG_FIVE" :key="trait.key" class="trait-row">
            <span class="trait-label dim">{{ trait.label }}</span>
            <div class="trait-bar-track">
              <div class="trait-bar-fill" :style="{ width: `${(agent[trait.key] || 0) * 100}%` }"></div>
            </div>
            <span class="trait-val">{{ ((agent[trait.key] || 0) * 100).toFixed(0) }}</span>
          </div>
        </div>
      </div>

      <!-- Belief Vector -->
      <div class="section" v-if="beliefs.length">
        <div class="section-title">Belief Vector</div>
        <div class="belief-list">
          <div v-for="belief in beliefs" :key="belief.topic" class="belief-row">
            <span class="belief-topic">{{ belief.topic }}</span>
            <div class="belief-bar-track">
              <div class="belief-bar-fill" :style="beliefBarStyle(belief.value)"></div>
              <div class="belief-center"></div>
            </div>
            <span class="belief-val" :style="{ color: belief.value > 0 ? 'var(--green)' : 'var(--red)' }">
              {{ belief.value > 0 ? '+' : '' }}{{ belief.value.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmotionBar from './EmotionBar.vue'
import PoliticalLean from './PoliticalLean.vue'

const props = defineProps({ agent: Object })
defineEmits(['close'])

const BIG_FIVE = [
  { key: 'openness', label: 'Openness' },
  { key: 'conscientiousness', label: 'Conscientiousness' },
  { key: 'extraversion', label: 'Extraversion' },
  { key: 'agreeableness', label: 'Agreeableness' },
  { key: 'neuroticism', label: 'Neuroticism' },
]

const beliefs = computed(() => {
  const bv = props.agent?.belief_vector || {}
  return Object.entries(bv).map(([topic, value]) => ({ topic, value }))
})

function beliefBarStyle(v) {
  if (v >= 0) {
    return { left: '50%', width: `${v * 50}%`, background: 'var(--green)' }
  } else {
    return { right: '50%', width: `${Math.abs(v) * 50}%`, background: 'var(--red)' }
  }
}
</script>

<style scoped>
.inspector {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.inspector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.inspector-title { display: flex; flex-direction: column; gap: 6px; }
.inspector-title h2 { font-size: 20px; }

.close-btn {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 24px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  transition: color var(--transition);
}
.close-btn:hover { color: var(--text-bright); }

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.meta-item.full { grid-column: 1 / -1; }
.meta-item .dim { font-size: 10px; }
.accent { color: var(--accent); }

.emotion-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
}
.emotion-row .dim { min-width: 55px; }

.trait-list { display: flex; flex-direction: column; gap: 8px; }
.trait-row { display: flex; align-items: center; gap: 10px; }

.trait-label { min-width: 110px; font-size: 11px; }

.trait-bar-track {
  flex: 1;
  height: 6px;
  background: var(--bg-4);
  border-radius: 3px;
  overflow: hidden;
}

.trait-bar-fill {
  height: 100%;
  background: var(--purple);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.trait-val {
  font-size: 11px;
  min-width: 28px;
  text-align: right;
  color: var(--purple);
}

.belief-list { display: flex; flex-direction: column; gap: 8px; }
.belief-row { display: flex; align-items: center; gap: 8px; }

.belief-topic {
  font-size: 11px;
  min-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.belief-bar-track {
  flex: 1;
  height: 6px;
  background: var(--bg-4);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.belief-bar-fill {
  position: absolute;
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.belief-center {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border-bright);
}

.belief-val { font-size: 11px; min-width: 40px; text-align: right; }
</style>
