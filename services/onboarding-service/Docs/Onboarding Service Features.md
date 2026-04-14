Onboarding Service Features
Here's the complete feature list for the onboarding service:

📋 Core Onboarding Management
Onboarding Status Tracking — Track company onboarding progress across 4 states:

NOT_STARTED
IN_PROGRESS
WIZARD_COMPLETE
FULLY_ONBOARDED
Step-Based Onboarding — 5 default mandatory steps:

Set up departments
Configure leave policies
Set attendance policy
Configure salary structure
Add first employee
Progress Calculation — Automatically calculate completion percentage based on completed/skipped steps

✅ Step Management
Complete Steps — Mark individual steps as completed or skipped
Skip Steps — Allow flexibility to skip non-critical steps
Retry Steps — Reset failed/completed steps back to pending for retry
Complete Wizard — Advance onboarding to WIZARD_COMPLETE status
📦 Template System
List Templates — Browse available region & category-specific seed templates
Apply Templates — Apply region-specific templates (leave types, salary structure) via orchestrated saga
Partial Failure Compensation — Rollback already-created resources on template application failure
📊 Analytics & Events
Event Publishing — Publish analytics events for:
onboarding.step_completed
onboarding.step_skipped
onboarding.wizard_completed
onboarding.completed
🔒 Data Integrity
Optimistic Locking — Prevent concurrent update conflicts
Idempotency — Event processing logs prevent duplicate processing
Role-Based Access Control — Different endpoints for SUPER_ADMIN, ADMIN, HR roles
🔗 Internal Service Integration
Service-to-Service API — Internal endpoint for auth-service to check onboarding status for COMPLETE_ONBOARDING action (JWT protected)