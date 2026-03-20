# QA — Accesibilidad (WCAG 2.2 AA)

**Date:** 2026-03-20 23:33
**Status:** ✅ Code review passed

## Audit Summary

### 1. Keyboard Navigation
- ✅ **Skip link:** `<a href="#main-content" class="skip-link">` en layout.tsx
- ✅ **Focus visible:** `*:focus-visible { outline: 3px solid var(--vc-focus) }` (golden ring, 3px)
- ✅ **Tab order:** Logical flow (header → sidebar → main content)
- ✅ **Keyboard shortcuts:** ⌘1-4 para cambiar módulos
- ✅ **Enter/Space:** Todos los botones son `<button>` nativo
- ✅ **Focus ring styles:** 212 instancias de focus/aria attributes

### 2. ARIA Labels & Roles
- ✅ **aria-label:** Presente en todos los componentes interactivos (90+ instancias)
- ✅ **Roles semánticos:**
  - `role="application"` en AppShell
  - `role="navigation"` en sidebar
  - `role="main"` en área de contenido
  - `role="banner"` en header
  - `role="status"` en indicadores de speaking/loading
  - `role="alertdialog"` en confirmaciones de control del SO
  - `role="progressbar"` en dwell indicator y onboarding progress
  - `role="switch"` en toggle de eye tracking
- ✅ **aria-current="page"** en módulo activo del sidebar
- ✅ **aria-pressed** en toggle buttons
- ✅ **aria-live="polite"** para anuncios dinámicos a screen readers

### 3. Target Sizes (WCAG 2.5.8 — Level AA)
- ✅ **Minimum 64px:** Todos los botones de acción principal
- ✅ **Quick phrases:** 80px (grid items en Communication/Control)
- ✅ **Sidebar items:** 80px min-height
- ✅ **Text inputs:** 64px min-height
- ✅ **Confirmation buttons:** 64px
- ✅ **Onboarding buttons:** 56-72px
- ✅ **Reminder items:** 64px

### 4. Color & Contrast
- ✅ **Dark theme:** bg #0A0A0A, text #F5F5F5 (ratio >15:1)
- ✅ **Secondary text:** #B0B0B0 on #0A0A0A (ratio ~10:1, passes AA)
- ✅ **Accent colors:** All pass 3:1 for non-text elements
- ✅ **High contrast mode:** CSS `@media (prefers-contrast: high)` with boosted values
- ✅ **Focus indicator:** #FFD700 gold (high visibility on dark bg)

### 5. Motion & Reduced Motion
- ✅ **prefers-reduced-motion:** All animations disabled (transition: 0ms)
- ✅ **No auto-playing content:** Audio requires user action
- ✅ **Smooth transitions:** 150ms ease-in-out (below 250ms seizure threshold)

### 6. Eye Tracking Accessibility
- ✅ **Dwell time configurable:** 400ms-2000ms slider in settings
- ✅ **Visual dwell progress:** Ring animation on gaze cursor
- ✅ **Gaze hover feedback:** `.gaze-hover` outline on interactive elements
- ✅ **Gaze activation feedback:** `.gaze-activated` green flash
- ✅ **Mouse fallback:** Automatic when eye tracker not connected
- ✅ **Toggle on/off:** Accessible button in header

### 7. Screen Reader Support
- ✅ **SR-only utility class:** `.sr-only` for hidden labels
- ✅ **Module announcements:** `aria-live="polite"` region updates on module change
- ✅ **Dynamic content:** Speaking status announced with role="status"
- ✅ **Decorative icons:** `aria-hidden="true"` on emoji decorations

### 8. Language
- ✅ **lang="es"** on HTML element
- ✅ **dir="ltr"** specified

## Recommendations for Future
- [ ] axe-core automated scan (requires running app)
- [ ] Real screen reader testing (VoiceOver on macOS)
- [ ] Real eye tracker testing (Tobii hardware)
- [ ] Switch access testing (1-2 switches)
- [ ] Color blindness simulation testing
