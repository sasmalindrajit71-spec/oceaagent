<template>
  <!-- frontend/src/views/SimulationDetail.vue -->
  <div class="page-bg">
    <div class="con-layout">

      <!-- LEFT: Agents -->
      <div class="c-col">
        <div class="col-label">Agents <span>{{ agents.length }} active</span></div>
        <div class="tick-box">
          <span class="tick-n">{{ tick }}</span>
          <span class="tick-s">/ 30 ticks</span>
        </div>
        <div class="ag-list">
          <div v-for="(a,i) in agents" :key="i"
               class="ag-row" :class="{sel: sel===i}" @click="sel=i">
            <div class="ag-av">{{ a.name.slice(0,2) }}</div>
            <div class="ag-info">
              <div class="ag-name">{{ a.name }}</div>
              <div class="ag-type">{{ a.type }}</div>
              <div class="ag-bar"><div class="ag-fill" :style="{width:a.belief+'%'}"></div></div>
            </div>
            <div class="ag-pct">{{ a.belief }}%</div>
          </div>
        </div>
      </div>

      <!-- CENTRE: Log -->
      <div class="c-main">
        <div class="col-label">Interaction Log <span>{{ ints.length }} events</span></div>
        <div v-for="(x,i) in ints" :key="i" class="int-row" :style="{animationDelay: i*0.06+'s'}">
          <div class="int-hdr">
            <span class="int-ag">{{ x.a1 }} × {{ x.a2 }}</span>
            <span class="int-t">T-{{ x.tick }}</span>
          </div>
          <p class="int-txt">{{ x.text }}</p>
          <span class="int-d" :class="x.pos?'pos':'neg'">{{ x.pos?'▲':'▼' }} {{ x.delta }}</span>
        </div>
      </div>

      <!-- RIGHT: Report -->
      <div class="c-col right">
        <div class="col-label">Intelligence Report</div>
        <div v-for="(r,i) in report" :key="i" class="rep-sec">
          <div class="rep-t">{{ r.title }}</div>
          <p v-if="r.text" class="rep-txt">{{ r.text }}</p>
          <div v-if="r.pred" class="rep-pred">{{ r.pred }}</div>
        </div>
        <div v-if="sel !== null" class="ag-detail">
          <div class="col-label" style="margin-bottom:.7rem">Agent Detail</div>
          <div class="ad-name">{{ agents[sel].name }}</div>
          <div class="ad-type">{{ agents[sel].type }}</div>
          <div style="height:1px;background:rgba(255,255,255,0.06);margin:1rem 0"></div>
          <div class="dr"><span>Belief score</span><span>{{ agents[sel].belief }}%</span></div>
          <div class="dr"><span>Interactions</span><span>{{ agents[sel].ints }}</span></div>
          <div class="dr"><span>Influence</span><span>{{ agents[sel].influence }}</span></div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const tick = ref(30)
const sel  = ref(0)
const agents = ref([
  { name:'PRIYA',  type:'Analyst',       belief:72, ints:8,  influence:'High'   },
  { name:'RAJAN',  type:'Traditionalist',belief:45, ints:5,  influence:'Medium' },
  { name:'ZARA',   type:'Progressive',   belief:88, ints:11, influence:'High'   },
  { name:'DEV',    type:'Pragmatist',    belief:55, ints:7,  influence:'Medium' },
  { name:'AMARA',  type:'Libertarian',   belief:33, ints:3,  influence:'Low'    },
  { name:'LEILA',  type:'Nationalist',   belief:91, ints:9,  influence:'High'   },
  { name:'KIRAN',  type:'Academic',      belief:62, ints:6,  influence:'Medium' },
  { name:'VIKRAM', type:'Skeptic',       belief:48, ints:4,  influence:'Low'    },
  { name:'MEERA',  type:'Empathist',     belief:76, ints:7,  influence:'Medium' },
])
const ints = ref([
  { a1:'PRIYA', a2:'RAJAN', tick:28, text:"Priya challenges Rajan's stance citing economic data. Rajan partially concedes on fiscal policy.",      delta:'+0.08', pos:true  },
  { a1:'ZARA',  a2:'DEV',   tick:26, text:"Climate reform debate. Zara's framing shifts Dev's neutrality toward moderate agreement.",              delta:'+0.14', pos:true  },
  { a1:'LEILA', a2:'AMARA', tick:24, text:'Fundamental disagreement on border policy. Both agents reinforce prior beliefs — no convergence.',      delta:'-0.03', pos:false },
  { a1:'KIRAN', a2:'PRIYA', tick:22, text:'Academic framing bridges analytical viewpoints. Collaborative consensus formed.',                      delta:'+0.21', pos:true  },
  { a1:'DEV',   a2:'RAJAN', tick:20, text:'Pragmatic approach finds common ground on economic nationalism. Belief alignment increases.',           delta:'+0.11', pos:true  },
  { a1:'MEERA', a2:'LEILA', tick:18, text:"Empathic reframing softens Leila's hard stance by 7 points. Emotional resonance effective.",           delta:'+0.07', pos:true  },
  { a1:'VIKRAM',a2:'ZARA',  tick:16, text:'Skeptic challenges evidence base. Zara maintains position but updates confidence rating downward.',     delta:'-0.05', pos:false },
])
const report = ref([
  { title:'Pattern Detection',  text:'Strong polarization between nationalist and progressive clusters. Analytical agents reduce fragmentation by 23% acting as bridge nodes.', pred: null },
  { title:'Causal Attribution', text:'Economic framing outperforms identity-based arguments. Memory decay accelerates centrist consensus post tick 20.', pred: null },
  { title:'Prediction',         text: null, pred:'High probability (78%) of moderate consensus within 10 additional ticks if pragmatist agents maintain bridging role.' },
])
</script>

<style scoped>
.page-bg {
  height: calc(100vh - 54px);
  background: rgba(0,0,0,0.82);
  overflow: hidden;
}
.con-layout {
  display: grid; grid-template-columns: 245px 1fr 265px;
  height: 100%;
}
.c-col {
  border-right: 1px solid rgba(255,255,255,0.07);
  padding: 1.4rem; overflow-y: auto;
}
.c-col.right { border-right: none; border-left: 1px solid rgba(255,255,255,0.07); }
.c-main { padding: 1.4rem; overflow-y: auto; display: flex; flex-direction: column; gap: 7px; }
.c-col::-webkit-scrollbar, .c-main::-webkit-scrollbar { width: 2px; }
.c-col::-webkit-scrollbar-thumb, .c-main::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
.col-label {
  font-family: 'Courier New', monospace; font-size: 9px;
  letter-spacing: 0.22em; text-transform: uppercase;
  color: rgba(255,255,255,0.22); margin-bottom: 1.2rem;
  display: flex; justify-content: space-between; flex-shrink: 0;
}
.tick-box {
  text-align: center; padding: 1.2rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 1.2rem;
}
.tick-n { font-family: 'Courier New', monospace; font-size: 2.8rem; font-weight: 700; color: #fff; line-height: 1; display: block; }
.tick-s { font-family: 'Courier New', monospace; font-size: 8px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.2); margin-top: 3px; }
.ag-list { display: flex; flex-direction: column; }
.ag-row {
  display: flex; align-items: center; gap: 8px; padding: 8px;
  border: 1px solid transparent; border-radius: 2px; cursor: pointer; transition: all 0.15s; margin-bottom: 2px;
}
.ag-row:hover, .ag-row.sel { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.08); }
.ag-av {
  width: 28px; height: 28px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.15);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Courier New', monospace; font-size: 9px; font-weight: 700;
  color: #fff; flex-shrink: 0; background: rgba(255,255,255,0.03);
}
.ag-info { flex: 1; min-width: 0; }
.ag-name { font-size: 11px; font-weight: 700; color: #fff; }
.ag-type { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.26); }
.ag-bar  { height: 1px; background: rgba(255,255,255,0.06); margin-top: 4px; }
.ag-fill { height: 100%; background: #fff; }
.ag-pct  { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.28); }
.int-row {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
  padding: 0.8rem; border-radius: 2px; animation: ii .3s both; flex-shrink: 0;
}
@keyframes ii { from{opacity:0;transform:translateX(-5px)} to{opacity:1;transform:none} }
.int-hdr { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.int-ag  { font-family: 'Courier New', monospace; font-size: 10px; color: #fff; font-weight: 700; }
.int-t   { font-family: 'Courier New', monospace; font-size: 8px; color: rgba(255,255,255,0.22); margin-left: auto; }
.int-txt { font-size: 11px; color: rgba(255,255,255,0.3); line-height: 1.6; }
.int-d   { display: inline-flex; align-items: center; gap: 3px; font-family: 'Courier New', monospace; font-size: 9px; margin-top: 5px; padding: 2px 7px; border-radius: 1px; border: 1px solid; }
.int-d.pos { color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1); }
.int-d.neg { color: rgba(255,255,255,0.28); background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.05); }
.rep-sec { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); padding: .8rem; border-radius: 2px; margin-bottom: 7px; }
.rep-t   { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.28); margin-bottom: 5px; }
.rep-txt { font-size: 11px; color: rgba(255,255,255,0.27); line-height: 1.68; }
.rep-pred { font-size: 11px; color: rgba(255,255,255,0.65); padding: 7px 10px; border-left: 1px solid rgba(255,255,255,0.22); background: rgba(255,255,255,0.03); margin-top: 5px; line-height: 1.6; }
.ag-detail { margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); }
.ad-name { font-size: 14px; font-weight: 700; color: #fff; }
.ad-type { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.25); margin-top: 2px; }
.dr { display: flex; justify-content: space-between; font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.22); padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.dr span:last-child { color: rgba(255,255,255,0.52); }
</style>