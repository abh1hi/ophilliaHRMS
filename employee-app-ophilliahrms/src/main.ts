import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import { md3 } from 'vuetify/blueprints'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import './index.css'
import App from './App.vue'

// ─── Saffron & White  –  Material Design 3 theme ─────────────────────────────
//  Primary   : #FF9933  (Saffron)
//  Background: #FFFBF5  (Warm white)
//  Surface   : #FFFFFF
// ─────────────────────────────────────────────────────────────────────────────

const vuetify = createVuetify({
  blueprint: md3,
  components,
  directives,
  theme: {
    defaultTheme: 'saffronLight',
    themes: {
      saffronLight: {
        dark: false,
        colors: {
          // ── Primary (Saffron) ──────────────────────────────────────────────
          primary:                   '#FF9933',
          'primary-darken-1':        '#E6841C',
          'primary-lighten-1':       '#FFB366',
          'primary-container':       '#FFEDCC',
          'on-primary':              '#FFFFFF',
          'on-primary-container':    '#4A2000',

          // ── Secondary (Deep Amber) ─────────────────────────────────────────
          secondary:                 '#B35C00',
          'secondary-darken-1':      '#8A4700',
          'secondary-container':     '#FFE0B2',
          'on-secondary':            '#FFFFFF',
          'on-secondary-container':  '#3E1800',

          // ── Surfaces & Background ─────────────────────────────────────────
          background:                '#FFFBF5',
          surface:                   '#FFFFFF',
          'surface-variant':         '#FFF3E0',
          'surface-bright':          '#FFFFFF',
          'on-surface':              '#1C1B1F',
          'on-surface-variant':      '#49454F',

          // ── Semantic ──────────────────────────────────────────────────────
          error:                     '#B3261E',
          'error-container':         '#F9DEDC',
          success:                   '#2E7D32',
          'success-container':       '#C8E6C9',
          warning:                   '#E65100',
          'warning-container':       '#FFE0B2',
          info:                      '#1565C0',
          'info-container':          '#BBDEFB',

          // ── Outline ───────────────────────────────────────────────────────
          outline:                   '#79747E',
          'outline-variant':         '#CAC4D0',
        },
      },
    },
  },
  defaults: {
    VCard:        { rounded: 'xl',  elevation: 1 },
    VBtn:         { rounded: 'xl',  elevation: 0 },
    VTextField:   { variant: 'outlined', rounded: 'lg', density: 'comfortable', color: 'primary' },
    VTextarea:    { variant: 'outlined', rounded: 'lg', density: 'comfortable', color: 'primary' },
    VSelect:      { variant: 'outlined', rounded: 'lg', density: 'comfortable', color: 'primary' },
    VChip:        { rounded: 'xl' },
    VAlert:       { rounded: 'xl' },
    VList:        { rounded: 'xl', bgColor: 'surface' },
  },
})

createApp(App).use(vuetify).mount('#app')
