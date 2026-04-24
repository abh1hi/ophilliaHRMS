# Shift Schedule Wizard - UI/UX Guide

## Visual Flow Overview

```
ShiftSchedulePanel Multi-Step Wizard
═════════════════════════════════════════════════════════════════

┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 1 of 6: Basic Info                                         │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ● ──○ ──○ ──○ ──○ ──○                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  📝 Define shift timing, duration, and settings               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Schedule Name*                                           │  │
│  │ [________________________________________]               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Shift Type*                                              │  │
│  │ [✓ Morning Shift   ▼]                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Description                                              │  │
│  │ [________________________________]                      │  │
│  │ [________________________________]                      │  │
│  │ [________________________________]                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│                                      [Cancel]  [Next ❯]        │
└───────────────────────────────────────────────────────────────┘


┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 2 of 6: Clock Windows                                     │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ✓ ──● ──○ ──○ ──○ ──○                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  ⏰ Define how early/late employees can clock in/out           │
│                                                                 │
│  📌 CLOCK-IN WINDOW                                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Minutes before shift start      Minutes after start   │  │
│  │  [10        ]                     [5         ]         │  │
│  │  Opens: 08:50 IST                Closes: 09:05 IST    │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  📌 CLOCK-OUT WINDOW                                           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Minutes before shift end        Minutes after end     │  │
│  │  [10        ]                     [10        ]         │  │
│  │  Opens: 16:50 IST                Closes: 17:10 IST    │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│              [❮ Previous]  [Cancel]  [Next ❯]                  │
└───────────────────────────────────────────────────────────────┘


┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 3 of 6: Locations                                         │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ✓ ──✓ ──● ──○ ──○ ──○                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  📍 Select the geofences where employees can clock in/out     │
│                                                                 │
│  CLOCK-IN LOCATIONS                                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🔍 Search and select clock-in locations...              │  │
│  │                                                         │  │
│  │ ✓ Main Office HQ                                        │  │
│  │ ✓ Branch - Delhi South                                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  CLOCK-OUT LOCATIONS                                           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🔍 Search and select clock-out locations...             │  │
│  │                                                         │  │
│  │ ✓ Main Office HQ                                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│              [❮ Previous]  [Cancel]  [Next ❯]                  │
└───────────────────────────────────────────────────────────────┘


┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 4 of 6: Off Days & Break                                  │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ✓ ──✓ ──✓ ──● ──○ ──○                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  📅 Define off days and when employees can take breaks         │
│                                                                 │
│  OFF DAYS (Select weekdays when clock-in is blocked)           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [Mon] [Tue] [Wed] [Thu] [Fri] [Sat] [Sun]              │  │
│  │                                   ■    ■                │  │
│  │                              (Saturday, Sunday selected) │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  BREAK WINDOW (Optional - for HR notifications)                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ If set, HR is notified when break starts outside window │  │
│  │                                                         │  │
│  │  Break Window Start    Break Window End                │  │
│  │  [12:00      ]         [13:00      ]                   │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│              [❮ Previous]  [Cancel]  [Next ❯]                  │
└───────────────────────────────────────────────────────────────┘


┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 5 of 6: Settings                                          │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ✓ ──✓ ──✓ ──✓ ──● ──○                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  ⚙️ Configure automatic clock-out and task requirements        │
│                                                                 │
│  AUTO CLOCK-OUT                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Auto Clock-Out Enabled         [☑]                     │  │
│  │  Auto Clock-Out At [17:00     ]                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  TASK MANAGEMENT                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Tasks Mandatory                [☐]                     │  │
│  │  Employees must log tasks                               │  │
│  │  before clocking out                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│              [❮ Previous]  [Cancel]  [Next ❯]                  │
└───────────────────────────────────────────────────────────────┘


┌─ Create Shift Schedule ────────────────────────────────────────┐
│ Step 6 of 6: Employees                                         │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step Progress: ✓ ──✓ ──✓ ──✓ ──✓ ──●                          │
│                 1   2   3   4   5   6                          │
│                                                                 │
│  👥 Assign employees and set the validity period              │
│                                                                 │
│  ASSIGNED EMPLOYEES                                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🔍 Search and select employees...                       │  │
│  │                                                         │  │
│  │ ✓ John Doe (EMP001)                                     │  │
│  │ ✓ Jane Smith (EMP002)                                   │  │
│  │ ✓ Mike Johnson (EMP003)                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  VALIDITY PERIOD                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Start Date*          End Date (Optional)               │  │
│  │  [2026-04-24      ]   [2026-06-24      ]               │  │
│  │  Schedule auto-extends 10 days if validity expires      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│              [❮ Previous]  [Cancel]  [✓ Create Schedule]       │
└───────────────────────────────────────────────────────────────┘
```

---

## Step Indicator Colors & States

### Step Number Badge
```
✓ (Green/Emerald)  - Completed step, can click to go back
● (Dark/Slate)     - Current step (active), cannot click
○ (Light/Slate)    - Future step, cannot click until previous complete
```

### Progress Bar
```
════○──○──○  - Current step: 2 of 6 (completed steps show green)
═══════════  - All steps complete (fully green)
```

---

## ShiftTypePanel Modal

```
┌─ New Shift Type ──────────────────────────────────────────────┐
│ Define shift timing, duration, and settings for this...        │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  ℹ️ Define the timing for this shift. Work hours per day...   │
│                                                                 │
│  Shift Name*                                                   │
│  [________________________________________]                   │
│                                                                 │
│  Start Time          End Time                                  │
│  [09:00]             [17:00]                                   │
│                                                                 │
│  Work Hours / Day         Break Duration (min)                │
│  [8     ]                 [30    ]                            │
│                                                                 │
│  Grace Period (min)                                            │
│  [5     ]                                                      │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ■ (Color)  Colour Label      Night Shift        ☐    │   │
│  │            Shown in roster                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Description                                                   │
│  [_____________________________]                               │
│  [_____________________________]                               │
│  [_____________________________]                               │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Active Status           Enable or disable    ☑          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
├───────────────────────────────────────────────────────────────┤
│                                      [Cancel]  [Save]         │
└───────────────────────────────────────────────────────────────┘
```

---

## Key UX Improvements

### Before (Single Form)
- ❌ Overwhelming number of fields on one screen
- ❌ Hard to know what to fill in order
- ❌ No progress indicator
- ❌ Long scrolling required
- ❌ Hard to edit specific sections

### After (Multi-Step Wizard)
- ✅ 1-2 focused sections per step
- ✅ Clear navigation flow
- ✅ Visual progress bar
- ✅ No scrolling (fits on screen)
- ✅ Easy to review and edit each section
- ✅ Reduced cognitive load
- ✅ Better for mobile screens
- ✅ Clear error messages per step

---

## Interaction Patterns

### Navigation
```
Step 1 ──Next──> Step 2 ──Next──> Step 3 ──Next──> Step 4 ──Next──> Step 5 ──Next──> Step 6
  ↑                 ↑                 ↑                ↑                 ↑                ↓
  └─Previous───────┘─Previous────────┘─Previous──────┘─Previous────────┘              Save
                                      (Can jump back to any previous step)
```

### Validation Flow
```
User fills Step 1 ──Validates──> If valid, Next enabled
                                 If invalid, Error shows, Next disabled

↓ (if form was previously invalid)

User fixes errors ──Revalidates──> If now valid, Next enabled
```

### Data Persistence
```
All form data persists during:
- Step navigation (forward & backward)
- Modal stays open

Data is ONLY saved when:
- User clicks "Save" on Step 6
- User confirms deletion

Data is LOST if:
- User closes modal without saving
- User clicks Cancel
- User leaves page
```

---

## Error Handling Examples

### Step 1 Error
```
❌ Schedule name is required
```

### Step 2 Error
```
❌ Shift type must be set first
```

### Step 6 Error
```
❌ Start date is required
```

---

## Mobile Responsiveness

The wizard is optimized for:
- ✅ Desktop (max-width: 48rem)
- ✅ Tablet (responsive grid to single column)
- ⚠️ Mobile (may require scroll on Step 3 with many locations)

---

## Keyboard Shortcuts (Future Enhancement)

| Key | Action |
|-----|--------|
| `Tab` | Navigate form fields |
| `Enter` | Submit step (if valid) |
| `Escape` | Close wizard |
| `←` `→` | Previous/Next step |

Currently not implemented - buttons must be clicked.

---

## Accessibility Features

- ✅ All inputs have associated labels
- ✅ Error messages announce with aria-live
- ✅ Form validation provides clear feedback
- ✅ Step indicator shows current progress
- ✅ High contrast colors for readability
- ✅ Adequate button sizes (h-10 = 40px minimum)
- ⚠️ TODO: Add ARIA labels for step indicator
- ⚠️ TODO: Keyboard shortcut support
- ⚠️ TODO: Screen reader testing

