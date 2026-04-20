<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Link, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  lat: number
  lng: number
  radius: number
}>()

const emit = defineEmits<{
  (e: 'update:lat', v: number): void
  (e: 'update:lng', v: number): void
  (e: 'update:radius', v: number): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
const googleMapsUrl = ref('')
const urlError = ref('')

let L: any = null
let map: any = null
let marker: any = null
let circle: any = null

async function initMap() {
  if (!mapContainer.value) return
  L = (await import('leaflet')).default

  // Fix Leaflet default icon paths broken by bundlers
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  })

  const lat = props.lat || 20.5937
  const lng = props.lng || 78.9629

  map = L.map(mapContainer.value).setView([lat, lng], props.lat ? 15 : 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)

  marker = L.marker([lat, lng], { draggable: true }).addTo(map)
  circle = L.circle([lat, lng], { radius: props.radius || 100, color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.12, weight: 2 }).addTo(map)

  marker.on('dragend', () => {
    const pos = marker.getLatLng()
    circle.setLatLng(pos)
    emit('update:lat', parseFloat(pos.lat.toFixed(6)))
    emit('update:lng', parseFloat(pos.lng.toFixed(6)))
  })

  map.on('click', (e: any) => {
    marker.setLatLng(e.latlng)
    circle.setLatLng(e.latlng)
    emit('update:lat', parseFloat(e.latlng.lat.toFixed(6)))
    emit('update:lng', parseFloat(e.latlng.lng.toFixed(6)))
  })
}

watch(() => props.radius, (r) => {
  if (circle) circle.setRadius(r)
})

watch(() => [props.lat, props.lng] as [number, number], ([lat, lng]) => {
  if (marker && lat && lng) {
    const latlng = [lat, lng]
    marker.setLatLng(latlng as any)
    circle.setLatLng(latlng as any)
    map.setView(latlng as any, map.getZoom())
  }
})

function parseGoogleMapsUrl() {
  urlError.value = ''
  const url = googleMapsUrl.value.trim()
  if (!url) return

  // Try ?q=lat,lng
  let m = url.match(/[?&]q=([-\d.]+),([-\d.]+)/)
  if (!m) m = url.match(/@([-\d.]+),([-\d.]+)/)
  if (!m) m = url.match(/\/([-\d.]+),([-\d.]+)/)

  if (m) {
    const lat = parseFloat(m[1])
    const lng = parseFloat(m[2])
    if (!isNaN(lat) && !isNaN(lng)) {
      emit('update:lat', lat)
      emit('update:lng', lng)
      return
    }
  }
  urlError.value = 'Could not extract coordinates from URL. Try a URL like: https://maps.google.com/?q=28.6139,77.2090'
}

onMounted(async () => {
  await nextTick()
  await initMap()
})

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})
</script>

<template>
  <div class="space-y-3">
    <!-- Google Maps URL Parser -->
    <div class="flex gap-2">
      <div class="flex-1 relative">
        <Link class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          v-model="googleMapsUrl"
          type="url"
          placeholder="Paste Google Maps URL to auto-fill location…"
          class="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-1.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pl-9"
          @keydown.enter.prevent="parseGoogleMapsUrl"
        />
      </div>
      <button
        type="button"
        @click="parseGoogleMapsUrl"
        class="h-9 px-4 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shrink-0"
      >
        Extract
      </button>
    </div>
    <p v-if="urlError" class="flex items-center gap-1.5 text-[11px] text-rose-600 font-medium">
      <AlertCircle class="w-3.5 h-3.5" />{{ urlError }}
    </p>
    <p v-else class="text-[10px] text-slate-400">Or click on the map / drag the marker to set location</p>

    <!-- Map -->
    <div ref="mapContainer" class="w-full h-72 rounded-2xl border border-slate-200 overflow-hidden z-0 relative" style="z-index: 0;" />

    <!-- Radius slider -->
    <div class="space-y-1.5">
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-slate-700">Geofence Radius</span>
        <span class="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">{{ radius }}m</span>
      </div>
      <input
        type="range"
        :value="radius"
        min="50"
        max="1000"
        step="10"
        @input="$emit('update:radius', Number(($event.target as HTMLInputElement).value))"
        class="w-full h-1.5 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-600"
      />
      <p class="text-[10px] text-slate-400">Employees must check in within <strong>{{ radius }} meters</strong> of this location</p>
    </div>
  </div>
</template>
