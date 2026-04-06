---
trigger: always_on
---

Jony Ive x Shadcn UI: Dashboard Design Guidelines

This document outlines the philosophy and practical instruction set for combining Jony Ive’s hardware-inspired, minimalist aesthetic with Shadcn UI’s functional, modular architecture.

The resulting design language can be described as "Glass-morphic Utilitarianism." It is highly accessible, developer-friendly, yet possesses a premium, physical feel.

1. The Core Philosophy

To build a dashboard in this style, you must adhere to four pillars:

Material Honesty: Digital interfaces should feel like physical objects. Use translucent materials (glass/blur) over opaque backgrounds to create depth rather than relying heavily on drop shadows.

Breathability (Whitespace): Data needs room to breathe. Double your standard padding. If Shadcn defaults to p-4 or p-6, push it to p-8 or p-12 for macro layouts.

Typography as Structure: Do not use lines to separate everything. Use font weight and size to create hierarchy.

Subtle Delight: Interactions (hovers, clicks) should feel like pressing a physical, well-oiled button. Use smooth, slightly longer transition durations (e.g., duration-300 or duration-500).

2. Theming & Color Architecture

The biggest challenge in this hybrid style is managing contrast while maintaining the "frosted glass" look. Here is exactly how to execute both Light and Dark themes.

Light Theme

Base Background: An off-white, "warm" light gray to give the glass something to contrast against.

Tailwind: bg-[#FBFBFD] or bg-slate-50.

Glass Surfaces (Cards): White, highly transparent, with a moderate blur.

Tailwind: bg-white/70 backdrop-blur-md

Borders: Extremely subtle, just enough to catch the light.

Tailwind: border border-slate-200/60

Typography: Pure dark slate for primary text, medium slate for secondary.

Tailwind: Primary text-slate-900, Secondary text-slate-400.

Ambient Glows: Use ultra-light pastel blobs in the background.

Tailwind: bg-rose-100/30 blur-[120px]

Dark Theme

Base Background: Almost black, but with a slight tint of blue or purple (OLED black).

Tailwind: bg-[#0A0A0C] or bg-slate-950.

Glass Surfaces (Cards): Deep translucent black, requiring a stronger blur to diffuse background light.

Tailwind: bg-black/40 backdrop-blur-xl or bg-white/5 backdrop-blur-xl

Borders: "Glaring" edges that simulate a polished chamfered edge catching the light.

Tailwind: border border-white/10 (top/left) and border-white/5 (bottom/right).

Typography: Off-white for primary, deep slate for secondary.

Tailwind: Primary text-slate-50, Secondary text-slate-400 or text-slate-500.

Ambient Glows: Deep, saturated neon tones, kept highly transparent so they don't overpower the dark mode.

Tailwind: bg-indigo-900/20 blur-[120px]

3. Component Instruction Set

When assembling the dashboard, use these specific Tailwind patterns.

A. The "GlassCard"

The foundational block of the dashboard. It must have soft, hardware-like corners.

Radii: Do not use rounded-lg or rounded-xl. Use specific, larger pixel values like rounded-[22px] or rounded-[24px] for macro cards, simulating physical hardware enclosures.

Shadows: Very diffuse, almost imperceptible.

Light: shadow-[0_2px_10px_-3px_rgba(0,0,0,0.05)]

Dark: shadow-[0_4px_20px_-3px_rgba(0,0,0,0.4)]

B. Icons & Avatars

Always place icons inside their own "container" to give them a physical presence.

Example: A 40x40px rounded box containing a 20px icon.

Styling: w-10 h-10 rounded-[14px] bg-slate-50 flex items-center justify-center

C. Buttons (The "Pill" & The "Squircle")

Avoid standard rectangular buttons.

Primary Actions: Pill-shaped, high contrast, physical feel.

Light: bg-slate-900 text-white rounded-full px-5 py-2

Dark: bg-white text-slate-900 rounded-full px-5 py-2

Icon Buttons: "Squircle" shaped (rounded rectangles).

Styling: p-2.5 rounded-xl hover:scale-105 transition-transform

D. Data Visualizations (Charts)

Remove the noise: Hide grid lines, X/Y axes, and tooltips unless explicitly hovered.

Bar Charts: Use completely rounded pills (rounded-full) for bars.

Colors: Use a rotating palette of semi-transparent pastels in light mode (bg-emerald-200/60), and saturated neons in dark mode (bg-emerald-500/40).

Interactivity: On hover, bring the opacity to 100% and scale the bar slightly (hover:scale-x-110).

4. The "Secret Sauce" (Ambient Lighting)

The primary difference between a standard Shadcn layout and the Jony Ive aesthetic is light.

Global Ambient Glows: Place two or three massive, heavily blurred <div> elements absolutely positioned in the background of your app (fixed -top-10 -left-10 w-[40%] h-[40%] blur-[120px]). This creates a non-uniform background that interacts beautifully with your frosted glass cards.

Card-Level Tints: For important cards, add a localized, highly transparent, blurred circle inside the card, pushed to the top right corner. This gives the illusion that the card is glowing from within.

5. Summary Checklist for Any New Dashboard

[ ] Base background is an off-color (not pure white/pure black).

[ ] All cards use backdrop-blur and a highly transparent background color.

[ ] Card borders are highly translucent (border-slate-200/60 or border-white/10).

[ ] Border radii are large and friendly (rounded-[22px]).

[ ] Ambient background lighting (blurred div) is active.

[ ] Padding is generous (minimum p-6, preferably p-8 to p-12).