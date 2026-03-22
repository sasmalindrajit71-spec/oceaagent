<template>
  <canvas ref="canvas" class="ocean-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

const canvas = ref(null)
let animId = null

onMounted(() => { init() })
onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })

function init() {
  const W = window.innerWidth
  const H = window.innerHeight

  const renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true, alpha: false })
  renderer.setSize(W, H)
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 1)

  const scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x000000, 0.032)

  const cam = new THREE.PerspectiveCamera(60, W / H, 0.1, 200)
  cam.position.set(0, 10, 24)
  cam.lookAt(0, 0, 0)

  const GS = 80
  const geo  = new THREE.PlaneGeometry(72, 72, GS, GS)
  const sgeo = new THREE.PlaneGeometry(72, 72, GS, GS)
  geo.rotateX(-Math.PI / 2)
  sgeo.rotateX(-Math.PI / 2)

  const wireOcean = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.04 }))
  wireOcean.position.y = -3
  scene.add(wireOcean)

  const solidOcean = new THREE.Mesh(sgeo, new THREE.MeshPhongMaterial({ color: 0x050505, specular: 0x151515, shininess: 90, transparent: true, opacity: 0.96, side: THREE.DoubleSide }))
  solidOcean.position.y = -3.02
  scene.add(solidOcean)

  const posAttr  = geo.attributes.position
  const sposAttr = sgeo.attributes.position
  const origY = new Float32Array(posAttr.count)
  for (let i = 0; i < posAttr.count; i++) origY[i] = posAttr.getY(i)

  scene.add(new THREE.AmbientLight(0xffffff, 0.05))
  const spotLight = new THREE.SpotLight(0xffffff, 1.8, 60, Math.PI / 5, 0.4)
  spotLight.position.set(0, 18, 0)
  scene.add(spotLight)
  const pointLight = new THREE.PointLight(0xffffff, 1.6, 36)
  pointLight.position.set(0, 7, 0)
  scene.add(pointLight)

  const agentPositions = [[-7,0,-5],[5,0,-7],[-3,0,2],[7,0,3],[0,0,-9],[-10,0,0],[9,0,-3],[2,0,7],[-6,0,8]]
  const agents = []
  agentPositions.forEach(p => {
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.18, 10, 10),
      new THREE.MeshPhongMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.6, transparent: true, opacity: 0.82 })
    )
    mesh.position.set(p[0], p[1] + 3 + Math.random() * 1.8, p[2])
    mesh.userData = { baseY: mesh.position.y, phase: Math.random() * Math.PI * 2 }
    scene.add(mesh)
    agents.push(mesh)
  })

  const lineGroup = new THREE.Group()
  scene.add(lineGroup)
  function rebuildLines() {
    while (lineGroup.children.length) lineGroup.remove(lineGroup.children[0])
    for (let i = 0; i < agents.length; i++) {
      for (let j = i + 1; j < agents.length; j++) {
        const d = agents[i].position.distanceTo(agents[j].position)
        if (d < 13) {
          lineGroup.add(new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([agents[i].position.clone(), agents[j].position.clone()]),
            new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.025 * (1 - d / 13) })
          ))
        }
      }
    }
  }

  function makeFish(scale) {
    const g    = new THREE.Group()
    const bmat = new THREE.MeshPhongMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.1, transparent: true, opacity: 0.45, side: THREE.DoubleSide })

    const body = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.65, 6), bmat.clone())
    body.rotation.z = -Math.PI / 2
    g.add(body)

    const tail = new THREE.Mesh(
      new THREE.ConeGeometry(0.16, 0.28, 4),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.28, side: THREE.DoubleSide })
    )
    tail.rotation.z = Math.PI / 2
    tail.position.x = -0.44
    g.add(tail)

    const fin = new THREE.Mesh(
      new THREE.ConeGeometry(0.07, 0.18, 3),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22, side: THREE.DoubleSide })
    )
    fin.position.set(0.05, 0.18, 0)
    g.add(fin)

    g.scale.setScalar(scale)
    return g
  }

  const SCHOOLS = 6
  const FISH_PER = 8
  const depthZones = [{ y: 0.5, spread: 1.0 }, { y: -2.5, spread: 1.2 }, { y: -5.5, spread: 0.8 }]
  const schools = []

  for (let s = 0; s < SCHOOLS; s++) {
    const ang  = Math.random() * Math.PI * 2
    const zone = depthZones[s % 3]
    const sch  = {
      x: (Math.random() - 0.5) * 46,
      y: zone.y + (Math.random() - 0.5) * zone.spread * 2,
      z: (Math.random() - 0.5) * 46,
      dx: Math.cos(ang), dz: Math.sin(ang),
      speed: 0.025 + Math.random() * 0.022,
      turnTimer: 80 + Math.floor(Math.random() * 160),
      fish: []
    }
    for (let f = 0; f < FISH_PER; f++) {
      const fish = makeFish(0.55 + Math.random() * 0.25)
      fish.userData = { ox: (Math.random()-0.5)*4.5, oy: (Math.random()-0.5)*1.8, oz: (Math.random()-0.5)*4.5, ph: Math.random()*Math.PI*2, spd: 3.0+Math.random()*2.2 }
      scene.add(fish)
      sch.fish.push(fish)
    }
    schools.push(sch)
  }

  let camAngle = 0
  const clock  = new THREE.Clock()
  let frame    = 0

  function animate() {
    animId = requestAnimationFrame(animate)
    const t = clock.getElapsedTime()
    frame++

    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i), z = posAttr.getZ(i)
      const w = Math.sin(x*0.38+t*0.9)*0.55 + Math.sin(z*0.32+t*0.72)*0.42 + Math.sin((x+z)*0.19+t*1.1)*0.28 + Math.cos(x*0.12+t*0.45)*0.20
      posAttr.setY(i, origY[i] + w)
      sposAttr.setY(i, origY[i] + w)
    }
    posAttr.needsUpdate  = true
    sposAttr.needsUpdate = true
    geo.computeVertexNormals()
    sgeo.computeVertexNormals()

    agents.forEach(m => {
      m.position.y = m.userData.baseY + Math.sin(t * 0.65 + m.userData.phase) * 0.65
      m.rotation.y += 0.005
      const p = 0.5 + 0.5 * Math.sin(t * 1.7 + m.userData.phase)
      m.material.emissiveIntensity = 0.22 + p * 0.65
    })
    if (frame % 12 === 0) rebuildLines()

    schools.forEach(sch => {
      sch.x += sch.dx * sch.speed
      sch.z += sch.dz * sch.speed
      if (sch.x >  46) sch.x = -46
      if (sch.x < -46) sch.x =  46
      if (sch.z >  46) sch.z = -46
      if (sch.z < -46) sch.z =  46

      sch.turnTimer--
      if (sch.turnTimer <= 0) {
        const na = Math.atan2(sch.dz, sch.dx) + (Math.random() - 0.5) * 1.4
        sch.dx = Math.cos(na)
        sch.dz = Math.sin(na)
        sch.turnTimer = 80 + Math.floor(Math.random() * 180)
      }

      const dirAngle = -Math.atan2(sch.dz, sch.dx)
      sch.fish.forEach(fish => {
        const { spd, ph, ox, oy, oz } = fish.userData
        fish.position.set(sch.x + ox + Math.sin(t*spd+ph)*0.08, sch.y + oy + Math.sin(t*spd*0.4+ph)*0.25, sch.z + oz)
        fish.rotation.y = dirAngle + Math.sin(t * spd + ph) * 0.04
        fish.children[1].rotation.x = Math.sin(t * spd * 1.6 + ph) * 0.42
      })
    })

    camAngle += 0.0011
    cam.position.x = Math.sin(camAngle) * 22
    cam.position.z = Math.cos(camAngle) * 22
    cam.position.y = 10 + Math.sin(t * 0.15) * 2.0
    cam.lookAt(0, 1, 0)
    pointLight.position.x = Math.sin(t * 0.36) * 10
    pointLight.position.z = Math.cos(t * 0.30) * 10

    renderer.render(scene, cam)
  }

  animate()
  rebuildLines()

  window.addEventListener('resize', () => {
    const nW = window.innerWidth, nH = window.innerHeight
    cam.aspect = nW / nH
    cam.updateProjectionMatrix()
    renderer.setSize(nW, nH)
  })
}
</script>

<style scoped>
.ocean-canvas {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  display: block;
}
</style>