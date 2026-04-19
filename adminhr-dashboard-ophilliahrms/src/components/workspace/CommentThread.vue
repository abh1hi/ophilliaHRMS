<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  Reply, 
  Pencil, 
  Trash2, 
  Send, 
  MessageSquare,
  MoreVertical,
  Activity,
  CheckCircle2,
  Clock,
  User,
  ShieldCheck,
  Zap
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  listComments, 
  addComment, 
  editComment, 
  deleteComment as apiDeleteComment 
} from '@/services/calendar-tasks.service'
import type { TaskComment } from '@/services/calendar-tasks.service'

interface Props {
  taskId: string
  currentUserId?: string
}

const props = defineProps<Props>()

const comments = ref<TaskComment[]>([])
const newBody = ref('')
const replyingTo = ref<string | null>(null)
const replyBody = ref('')
const editingComment = ref<TaskComment | null>(null)
const editBody = ref('')

const topLevel = computed(() => comments.value.filter(c => !c.parent_comment_id && c.status !== 'deleted'))
const replies = (parentId: string) => comments.value.filter(c => c.parent_comment_id === parentId && c.status !== 'deleted')

function canEdit(c: TaskComment) {
  return !props.currentUserId || c.author_id === props.currentUserId
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

onMounted(async () => {
  comments.value = (await listComments(props.taskId)) ?? []
})

async function submitNew() {
  if (!newBody.value.trim()) return
  const c = await addComment(props.taskId, newBody.value.trim())
  if (c) comments.value.push(c)
  newBody.value = ''
}

function startReply(parentId: string) {
  replyingTo.value = parentId
  replyBody.value = ''
}

async function submitReply(parentId: string) {
  if (!replyBody.value.trim()) return
  const c = await addComment(props.taskId, replyBody.value.trim(), parentId)
  if (c) comments.value.push(c)
  replyingTo.value = null
  replyBody.value = ''
}

function startEdit(c: TaskComment) {
  editingComment.value = c
  editBody.value = c.body
}

async function submitEdit() {
  if (!editingComment.value || !editBody.value.trim()) return
  const updated = await editComment(props.taskId, editingComment.value.id, editBody.value.trim())
  if (updated) {
    const idx = comments.value.findIndex(c => c.id === updated.id)
    if (idx !== -1) comments.value[idx] = updated
  }
  editingComment.value = null
}

async function deleteComment(id: string) {
  await apiDeleteComment(props.taskId, id)
  const idx = comments.value.findIndex(c => c.id === id)
  if (idx !== -1) comments.value[idx] = { ...comments.value[idx], status: 'deleted' }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Transmission Manifest -->
    <div v-if="comments.length" class="space-y-4">
      <div
        v-for="c in topLevel"
        :key="c.id"
        class="group/comment animate-in fade-in slide-in-from-left-2 duration-300"
      >
        <div class="flex gap-4">
          <!-- Identity Node -->
          <div class="w-9 h-9 rounded-xl bg-slate-900 border border-slate-800 shadow-lg flex items-center justify-center text-[11px] font-black text-white flex-shrink-0 transition-transform group-hover/comment:scale-105">
            {{ c.author_id.charAt(0).toUpperCase() }}
          </div>
          
          <div class="flex-1 space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-[11px] font-black text-slate-900 uppercase tracking-widest">{{ c.author_id }}</span>
                <span class="text-[9px] font-bold text-slate-400 uppercase tracking-tight">{{ formatTime(c.created_at) }}</span>
                <Badge v-if="c.status === 'edited'" variant="outline" class="h-4 px-1 text-[7px] border-slate-100 text-slate-300 uppercase font-black">Edited</Badge>
              </div>
            </div>

            <div class="bg-white border border-slate-100/60 rounded-[20px] px-4 py-3 text-sm text-slate-600 leading-relaxed shadow-sm group-hover/comment:border-slate-200 transition-all">
              {{ c.body }}
            </div>

            <!-- Interaction Protocols -->
            <div class="flex gap-4 mt-1 opacity-0 group-hover/comment:opacity-100 transition-all">
              <button @click="startReply(c.id)" class="text-[10px] font-black text-slate-400 hover:text-indigo-600 uppercase tracking-widest flex items-center gap-1.5 transition-colors">
                <Reply class="w-3 h-3" /> Reply
              </button>
              <button v-if="canEdit(c)" @click="startEdit(c)" class="text-[10px] font-black text-slate-400 hover:text-slate-900 uppercase tracking-widest flex items-center gap-1.5 transition-colors">
                <Pencil class="w-3 h-3" /> Edit
              </button>
              <button v-if="canEdit(c)" @click="deleteComment(c.id)" class="text-[10px] font-black text-slate-400 hover:text-rose-600 uppercase tracking-widest flex items-center gap-1.5 transition-colors">
                <Trash2 class="w-3 h-3" /> Delete
              </button>
            </div>

            <!-- Recursive Sub-Nodes -->
            <div v-if="replies(c.id).length" class="mt-4 ml-6 space-y-4 border-l-2 border-slate-100 pl-4">
              <div v-for="r in replies(c.id)" :key="r.id" class="flex gap-3 group/reply animate-in fade-in slide-in-from-top-1 duration-300">
                <div class="w-7 h-7 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-[10px] font-black text-slate-600 flex-shrink-0">
                  {{ r.author_id.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 space-y-1.5">
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-black text-slate-700 uppercase tracking-widest">{{ r.author_id }}</span>
                    <span class="text-[8px] font-bold text-slate-400 uppercase tracking-tight">{{ formatTime(r.created_at) }}</span>
                  </div>
                  <div class="bg-slate-50 border border-slate-100 rounded-[16px] px-3.5 py-2 text-[13px] text-slate-600 font-medium group-hover/reply:bg-white transition-colors">{{ r.body }}</div>
                </div>
              </div>
            </div>

            <!-- Modulation Input: Reply -->
            <div v-if="replyingTo === c.id" class="mt-4 ml-6 flex gap-3 animate-in slide-in-from-top-2 duration-300">
              <Input
                v-model="replyBody"
                placeholder="Initialize reply sequence..."
                class="h-10 rounded-xl bg-white border-slate-200 text-xs font-medium focus-visible:ring-indigo-500"
                @keyup.enter="submitReply(c.id)"
              />
              <Button @click="submitReply(c.id)" size="sm" class="h-10 rounded-xl px-4 bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-100 font-bold uppercase tracking-widest text-[9px]">
                <Send class="w-3 h-3 mr-2" />
                Commit
              </Button>
              <Button @click="replyingTo = null" variant="ghost" size="sm" class="h-10 rounded-xl px-4 text-slate-400 hover:text-slate-600 text-[9px] font-bold uppercase tracking-widest">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-10 px-6 rounded-[32px] bg-slate-50/50 border border-dashed border-slate-200 group">
      <MessageSquare class="w-8 h-8 text-slate-200 mb-3 group-hover:scale-110 transition-transform" />
      <p class="text-[11px] font-black text-slate-300 uppercase tracking-widest text-center">Transmission Void: No Communication Detected</p>
    </div>

    <!-- Modulation Input: Edit -->
    <div v-if="editingComment" class="p-4 bg-indigo-50/30 border border-indigo-100 rounded-[28px] flex gap-3 animate-in slide-in-from-bottom-2 duration-300">
      <Input
        v-model="editBody"
        class="h-11 rounded-2xl bg-white border-indigo-200 text-sm font-medium"
        @keyup.enter="submitEdit"
      />
      <Button @click="submitEdit" class="h-11 rounded-2xl px-6 bg-slate-900 text-white hover:bg-black shadow-lg shadow-slate-200 font-bold uppercase tracking-widest text-[10px]">
        Commit Changes
      </Button>
      <Button @click="editingComment = null" variant="ghost" class="h-11 rounded-2xl px-6 text-slate-500 font-bold uppercase tracking-widest text-[10px]">
        Abort
      </Button>
    </div>

    <!-- Initialization Input: New Comment -->
    <div v-else class="pt-6 border-t border-slate-100">
      <div class="flex gap-3">
        <Input
          v-model="newBody"
          placeholder="Inject comment metadata..."
          class="h-11 rounded-2xl bg-slate-50/50 border-slate-200 text-sm font-medium focus-visible:bg-white transition-all shadow-inner"
          @keyup.enter="submitNew"
        />
        <Button
          @click="submitNew"
          :disabled="!newBody.trim()"
          class="h-11 rounded-2xl px-8 bg-slate-900 text-white hover:bg-black shadow-xl shadow-slate-200 disabled:opacity-30 disabled:shadow-none font-bold uppercase tracking-widest text-[10px]"
        >
          <Zap class="w-3.5 h-3.5 mr-2" />
          Transmit
        </Button>
      </div>
    </div>
  </div>
</template>
