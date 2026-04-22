import type { Component } from 'vue'

export interface DocBlock {
  title: string
  bullets: string[]
}

export interface DocNavTab {
  label: string
  tab: string
}

export interface DocModule {
  id: string
  title: string
  summary: string
  category: string
  icon: Component
  audience: string[]
  navTabs?: DocNavTab[]
  blocks: DocBlock[]
}

export interface HelpFlow {
  title: string
  icon: Component
  points: string[]
}

export interface DocSidebarItem {
  id: string
  title: string
  category: string
  icon: Component
  summary: string
}

export interface HowToFlowStep {
  title: string
  detail: string
  expectedResult: string
  tab?: string
}

export interface HowToFlow {
  id: string
  title: string
  summary: string
  owner: string
  outcome: string
  prerequisites: string[]
  steps: HowToFlowStep[]
  checks: string[]
}
