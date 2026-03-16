<template>
  <v-container fluid class="pa-0 fill-height" style="background:#FFFBF5; min-height:100vh;">
    <v-row align="center" justify="center" class="fill-height ma-0">
      <v-col cols="12" sm="8" md="5" lg="4" class="px-6">

        <!-- Brand mark -->
        <div class="text-center mb-8">
          <div class="brand-circle d-flex align-center justify-center mx-auto mb-4">
            <v-icon size="40" color="white">mdi-flower-lotus-outline</v-icon>
          </div>
          <h1 class="text-h5 font-weight-bold" style="color:#1C1B1F; letter-spacing:-0.3px;">Ophillia HR</h1>
          <p class="text-body-2 mt-1" style="color:#49454F;">Employee Self-Service Portal</p>
        </div>

        <!-- Sign-in card -->
        <v-card elevation="0" rounded="xl" style="border:1px solid rgba(255,153,51,0.25);">
          <v-card-text class="pa-6">
            <p class="text-subtitle-1 font-weight-bold mb-5" style="color:#1C1B1F;">Sign in to continue</p>

            <v-form ref="formRef" @submit.prevent="submit">
              <v-text-field
                v-model="email"
                id="email-input"
                label="Work Email"
                type="email"
                prepend-inner-icon="mdi-email-outline"
                :rules="[v => !!v || 'Email required', v => /.+@.+/.test(v) || 'Invalid email']"
                autocomplete="email"
                class="mb-3"
              />
              <v-text-field
                v-model="password"
                id="password-input"
                label="Password"
                :type="showPw ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="showPw ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                @click:append-inner="showPw = !showPw"
                :rules="[v => !!v || 'Password required']"
                autocomplete="current-password"
                class="mb-2"
              />

              <v-alert v-if="error" type="error" variant="tonal" density="compact" rounded="xl" class="mb-4" icon="mdi-alert-circle-outline">
                {{ error }}
              </v-alert>

              <v-btn
                id="sign-in-btn"
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                rounded="xl"
                class="mt-1 text-none"
                style="font-weight:600; height:52px;"
              >Sign In</v-btn>

              <div class="text-center mt-4">
                <v-btn variant="text" size="small" color="primary" class="text-none">Forgot password?</v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

        <p class="text-caption text-center mt-5" style="color:#79747E;">Secure access · Ophillia HRMS</p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { login as apiLogin, getMyProfile } from '../services/api'

const emit = defineEmits<{ login: [data: any] }>()
const formRef  = ref<any>(null)
const email    = ref('')
const password = ref('')
const showPw   = ref(false)
const loading  = ref(false)
const error    = ref('')

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  error.value = ''
  loading.value = true
  try {
    const tokens = await apiLogin(email.value, password.value)
    localStorage.setItem('access_token', tokens.access_token)
    const profile = await getMyProfile()
    emit('login', { ...profile, ...tokens })
  } catch (e: any) {
    error.value = e.message ?? 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.brand-circle {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, #FF9933 0%, #E6841C 100%);
  box-shadow: 0 4px 20px rgba(255, 153, 51, 0.4);
}
</style>
