<template>
  <div class="space-y-3">
    <!-- Comments list -->
    <div v-if="comments.length" class="space-y-2">
      <div
        v-for="c in topLevel"
        :key="c.id"
        class="group"
      >
        <!-- Comment bubble -->
        <div class="flex gap-2.5">
          <div class="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium text-slate-600 flex-shrink-0">
            {{ c.author_id.charAt(0).toUpperCase() }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-medium text-slate-700">{{ c.author_id }}</span>
              <span class="text-xs text-slate-400">{{ formatTime(c.created_at) }}</span>
              <span v-if="c.status === 'edited'" class="text-xs text-slate-400">(edited)</span>
            </div>
            <div class="bg-slate-50 rounded-lg px-3 py-2 text-sm text-slate-700 leading-relaxed">
              {{ c.body }}
            </div>
            <!-- Actions -->
            <div class="flex gap-3 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button @click="startReply(c.id)" class="text-xs text-slate-400 hover:text-slate-600">Reply</button>
              <button v-if="canEdit(c)" @click="startEdit(c)" class="text-xs text-slate-400 hover:text-slate-600">Edit</button>
              <button v-if="canEdit(c)" @click="deleteComment(c.id)" class="text-xs text-slate-400 hover:text-red-500">Delete</button>
            </div>

            <!-- Replies -->
            <div v-if="replies(c.id).length" class="mt-2 ml-4 space-y-2">
              <div v-for="r in replies(c.id)" :key="r.id" class="flex gap-2">
                <div class="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium text-slate-600 flex-shrink-0">
                  {{ r.author_id.charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-0.5">
                    <span class="text-xs font-medium text-slate-700">{{ r.author_id }}</span>
                    <span class="text-xs text-slate-400">{{ formatTime(r.created_at) }}</span>
                  </div>
                  <div class="bg-slate-50 rounded-lg px-2.5 py-1.5 text-sm text-slate-700">{{ r.body }}</div>
                </div>
              </div>
            </div>

            <!-- Reply input -->
            <div v-if="replyingTo === c.id" class="mt-2 ml-4 flex gap-2">
              <input
                v-model="replyBody"
                type="text"
                placeholder="Write a reply…"
                class="flex-1 px-2.5 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-slate-400"
                @keyup.enter="submitReply(c.id)"
              />
              <button @click="submitReply(c.id)" class="px-2 py-1.5 text-xs bg-slate-900 text-white rounded-lg">Send</button>
              <button @click="replyingTo = null" class="px-2 py-1.5 text-xs text-slate-500 hover:text-slate-700">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p v-else class="text-sm text-slate-400 text-center py-4">No comments yet. Be the first to comment.</p>

    <!-- Edit inline -->
    <div v-if="editingComment" class="flex gap-2">
      <input
        v-model="editBody"
        type="text"
        class="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
        @keyup.enter="submitEdit"
      />
      <button @click="submitEdit" class="px-3 py-2 text-sm bg-slate-900 text-white rounded-lg">Save</button>
      <button @click="editingComment = null" class="px-3 py-2 text-sm text-slate-500 hover:text-slate-700">Cancel</button>
    </div>

    <!-- New comment -->
    <div class="flex gap-2 pt-2 border-t border-slate-100">
      <input
        v-model="newBody"
        type="text"
        placeholder="Add a comment…"
        class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
        @keyup.enter="submitNew"
      />
      <button
        @click="submitNew"
        :disabled="!newBody.trim()"
        class="px-3 py-2 text-sm bg-slate-900 text-white rounded-lg hover:bg-slate-700 disabled:opacity-40"
      >
        Post
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listComments, addComment, editComment, deleteComment as apiDeleteComment } from '@/services/calendar-tasks.service'
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
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
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
