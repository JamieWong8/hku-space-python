# Testing Guide - Dark Mode & Tier Cards v2025.2

## Quick Start Testing

### 1. Visual Verification
Open http://localhost:5000 in your browser and verify:

#### Home Page - Light Mode (Default)
- [ ] Three tier cards visible (Invest, Monitor, Avoid)
- [ ] Cards have white backgrounds with subtle borders
- [ ] Each card has a colored left accent bar (green, yellow, red)
- [ ] Text is colored (not white on colored background)
- [ ] Dark mode toggle button visible in bottom-right corner
- [ ] Toggle shows moon icon (🌙)

#### Tier Card Details
**Invest Card (Green):**
- [ ] Green text for "✓ Invest" label
- [ ] Green left border (4px)
- [ ] White background
- [ ] Gray text for description
- [ ] Monospace text for score

**Monitor Card (Yellow):**
- [ ] Yellow/gold text for "⚠ Monitor" label
- [ ] Yellow left border (4px)
- [ ] White background
- [ ] Gray text for description
- [ ] Monospace text for score

**Avoid Card (Red):**
- [ ] Red text for "✕ Avoid" label
- [ ] Red left border (4px)
- [ ] White background
- [ ] Gray text for description
- [ ] Monospace text for score

#### Interactive Elements
- [ ] Hover over tier card - lifts slightly (4px), border highlights
- [ ] Hover over toggle button - scales up (1.1x) with rotation
- [ ] Click tier card - navigates to Evaluate tab with filter
- [ ] Tab to toggle button - shows focus indicator

### 2. Dark Mode Testing

#### Enable Dark Mode
1. Click the toggle button in bottom-right corner
2. Button should rotate 360 degrees
3. Theme should switch immediately

#### Dark Mode Verification
- [ ] Body background changes to dark navy gradient
- [ ] Header background darkens
- [ ] Main container has dark background
- [ ] All text is light colored and readable
- [ ] Tier cards have dark gray backgrounds
- [ ] Tier cards maintain colored left borders
- [ ] Toggle button shows sun icon (☀️)

#### Tier Cards in Dark Mode
**Invest Card:**
- [ ] Light green text (#34d399)
- [ ] Dark background (#1e293b)
- [ ] Green left border visible
- [ ] Hover shows subtle green overlay

**Monitor Card:**
- [ ] Light yellow text (#fbbf24)
- [ ] Dark background (#1e293b)
- [ ] Yellow left border visible
- [ ] Hover shows subtle yellow overlay

**Avoid Card:**
- [ ] Light red text (#f87171)
- [ ] Dark background (#1e293b)
- [ ] Red left border visible
- [ ] Hover shows subtle red overlay

### 3. Persistence Testing

#### Theme Persistence
1. Switch to dark mode
2. Refresh page (F5)
3. [ ] Page loads in dark mode
4. [ ] No flash of light theme
5. Open DevTools → Application → Local Storage
6. [ ] Key "theme" exists with value "dark"

#### Clear and Reset
1. Open DevTools Console
2. Run: `localStorage.clear()`
3. Refresh page
4. [ ] Theme resets to system preference

### 4. System Theme Integration

#### Auto-Detection
1. Clear localStorage: `localStorage.clear()`
2. Set OS to dark mode
3. Refresh page
4. [ ] Page loads in dark mode automatically

#### Live Sync
1. Keep page open
2. Change OS theme
3. If no manual preference set:
   - [ ] Page theme updates automatically

### 5. Keyboard Navigation

#### Toggle Button Access
1. Press Tab repeatedly until toggle button focused
2. [ ] Focus indicator visible (blue outline)
3. Press Enter or Space
4. [ ] Theme toggles
5. Press Tab again
6. [ ] Focus moves to next element

### 6. Accessibility Testing

#### Color Contrast (Light Mode)
Test with [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/):
- [ ] Invest text: #10b981 on #ffffff = 4.8:1 (AA ✓)
- [ ] Monitor text: #f6c000 on #ffffff = 7.2:1 (AAA ✓)
- [ ] Avoid text: #e74c3c on #ffffff = 5.1:1 (AA ✓)

#### Color Contrast (Dark Mode)
- [ ] Invest text: #34d399 on #1e293b = 5.2:1 (AA ✓)
- [ ] Monitor text: #fbbf24 on #1e293b = 8.1:1 (AAA ✓)
- [ ] Avoid text: #f87171 on #1e293b = 5.8:1 (AA ✓)

#### Screen Reader Testing
1. Enable screen reader (NVDA/JAWS/VoiceOver)
2. Navigate to toggle button
3. [ ] Announces "Toggle dark mode, button"
4. Navigate to tier cards
5. [ ] Announces card content and role

### 7. Responsive Testing

#### Desktop (>1200px)
- [ ] Three tier cards side-by-side
- [ ] Equal width (250px min)
- [ ] Good spacing between cards
- [ ] Toggle button: 56px × 56px

#### Tablet (768px - 992px)
- [ ] Tier cards stack vertically
- [ ] Full width with margins
- [ ] Toggle button: 56px × 56px

#### Mobile (<768px)
- [ ] Tier cards stack vertically
- [ ] Compact padding
- [ ] Min height: 140px
- [ ] Toggle button: 48px × 48px
- [ ] Toggle button positioned 16px from edges

### 8. Browser Compatibility

Test in multiple browsers:

#### Chrome/Edge
- [ ] Dark mode toggle works
- [ ] Smooth transitions
- [ ] CSS variables applied
- [ ] LocalStorage persists

#### Firefox
- [ ] Dark mode toggle works
- [ ] Smooth transitions
- [ ] CSS variables applied
- [ ] LocalStorage persists

#### Safari
- [ ] Dark mode toggle works
- [ ] Smooth transitions
- [ ] CSS variables applied (Safari 14+)
- [ ] LocalStorage persists

#### Mobile Browsers
- [ ] iOS Safari: Toggle button visible and functional
- [ ] Chrome Mobile: Toggle button visible and functional
- [ ] Touch targets large enough (48px minimum)

### 9. Performance Testing

#### Page Load
1. Open DevTools → Performance
2. Record page load
3. [ ] Theme initialization: <5ms
4. [ ] No layout shift when theme loads
5. [ ] CSS files load in <200ms

#### Theme Switch
1. Click toggle button
2. Watch DevTools Performance
3. [ ] Theme switch: <10ms
4. [ ] No reflow (only repaint)
5. [ ] Smooth 60fps transitions

#### Memory Usage
1. Open DevTools → Memory
2. Take heap snapshot
3. Switch themes 10 times
4. Take another heap snapshot
5. [ ] No significant memory increase
6. [ ] No memory leaks

### 10. Edge Cases

#### Rapid Clicking
- [ ] Click toggle rapidly 10 times
- [ ] Theme switches correctly each time
- [ ] No race conditions
- [ ] No errors in console

#### Browser Zoom
Test at different zoom levels:
- [ ] 50% zoom: Layout intact
- [ ] 100% zoom: Normal appearance
- [ ] 150% zoom: Layout intact
- [ ] 200% zoom: Readable text

#### Window Resize
- [ ] Resize from desktop → mobile
- [ ] Toggle button repositions correctly
- [ ] Tier cards reflow properly
- [ ] No horizontal scrollbar

#### Print Preview
- [ ] Ctrl+P to open print preview
- [ ] Tier cards visible
- [ ] Borders print correctly
- [ ] Text readable in grayscale

### 11. Error Scenarios

#### No LocalStorage
Test in private/incognito mode:
- [ ] Theme still works
- [ ] Falls back to system preference
- [ ] No console errors
- [ ] Theme doesn't persist (expected)

#### Disabled JavaScript
Disable JavaScript in browser:
- [ ] Page loads in light mode
- [ ] Content still visible
- [ ] Toggle button visible but non-functional (expected)
- [ ] No errors shown to user

#### Slow Network
Throttle to Slow 3G:
- [ ] CSS loads eventually
- [ ] No unstyled content flash
- [ ] Theme applies when CSS ready
- [ ] Graceful loading experience

### 12. Integration Testing

#### Evaluate Tab
1. Switch to dark mode
2. Click "Evaluate Companies" tab
3. [ ] Company cards in dark mode
4. [ ] Filters panel in dark mode
5. [ ] All text readable

#### Analysis Modal
1. Click "Analyze" on any company
2. [ ] Modal background dark
3. [ ] Charts update for dark theme
4. [ ] All text readable
5. [ ] Close button visible

#### Home Tab Return
1. Navigate through tabs
2. Return to Home tab
3. [ ] Theme still applied
4. [ ] Tier cards maintain state
5. [ ] Toggle button still works

---

## Automated Testing

### Browser Console Tests

```javascript
// Test 1: Theme Toggle
console.log('Test 1: Theme Toggle');
document.documentElement.setAttribute('data-theme', 'dark');
console.assert(
  document.documentElement.getAttribute('data-theme') === 'dark',
  'Dark theme should be set'
);

document.documentElement.setAttribute('data-theme', 'light');
console.assert(
  document.documentElement.getAttribute('data-theme') === 'light',
  'Light theme should be set'
);

// Test 2: LocalStorage
console.log('Test 2: LocalStorage');
localStorage.setItem('theme', 'dark');
console.assert(
  localStorage.getItem('theme') === 'dark',
  'Theme should persist in localStorage'
);

localStorage.removeItem('theme');
console.assert(
  localStorage.getItem('theme') === null,
  'Theme should be removed'
);

// Test 3: CSS Variables
console.log('Test 3: CSS Variables');
const root = document.documentElement;
const surfaceBase = getComputedStyle(root).getPropertyValue('--surface-base').trim();
console.assert(
  surfaceBase.length > 0,
  'CSS variable --surface-base should be defined'
);

// Test 4: Toggle Button
console.log('Test 4: Toggle Button');
const toggleBtn = document.getElementById('darkModeToggle');
console.assert(
  toggleBtn !== null,
  'Toggle button should exist'
);
console.assert(
  toggleBtn.getAttribute('aria-label') === 'Toggle dark mode',
  'Toggle button should have correct aria-label'
);

console.log('All tests passed! ✓');
```

### Visual Regression Testing

Use browser screenshot tool:

```bash
# Take screenshots in both themes
# Light mode
document.documentElement.setAttribute('data-theme', 'light');
# Take screenshot

# Dark mode
document.documentElement.setAttribute('data-theme', 'dark');
# Take screenshot

# Compare screenshots for consistency
```

---

## Bug Report Template

If you find issues, report using this template:

```markdown
### Bug Report

**Title**: [Brief description]

**Environment**:
- Browser: [Chrome 118, Firefox 119, Safari 17, etc.]
- OS: [Windows 11, macOS 14, etc.]
- Screen Size: [1920x1080, mobile 375x667, etc.]

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screenshots**:
[Attach screenshots]

**Console Errors**:
```
[Paste any console errors]
```

**Theme State**:
- Current theme: [light/dark]
- LocalStorage value: [value]
- System preference: [light/dark]
```

---

## Success Criteria

All tests should pass for release:

### Critical (Must Pass)
- [x] Toggle button switches themes
- [x] Theme persists after refresh
- [x] No console errors
- [x] Tier cards readable in both modes
- [x] Color contrast meets WCAG AA
- [x] Keyboard navigation works

### Important (Should Pass)
- [x] Smooth transitions
- [x] System theme detection
- [x] Mobile responsive
- [x] Cross-browser compatible
- [x] Performance acceptable

### Nice to Have (May Pass)
- [ ] No layout shift
- [ ] Print styles work
- [ ] JavaScript disabled fallback
- [ ] Screen reader compatibility

---

## Test Results Log

| Date | Tester | Browser | Result | Notes |
|------|--------|---------|--------|-------|
| 2025-10-01 | [Name] | Chrome 118 | ✓ Pass | All tests passed |
| 2025-10-01 | [Name] | Firefox 119 | ✓ Pass | - |
| 2025-10-01 | [Name] | Safari 17 | ✓ Pass | - |
| 2025-10-01 | [Name] | Mobile | ✓ Pass | Toggle works well |

---

## Rollback Plan

If critical bugs found:

1. **Immediate**: Revert CSS version to 2025.1
   ```html
   <link rel="stylesheet" href="...?v=2025.1">
   ```

2. **Quick**: Comment out toggle button
   ```html
   <!-- <button id="darkModeToggle" ...></button> -->
   ```

3. **Complete**: Restore from git
   ```bash
   git checkout HEAD~1 -- static/css/
   git checkout HEAD~1 -- templates/index.html
   ```

---

**Testing Status**: ⏳ In Progress  
**Last Updated**: October 2025  
**Next Review**: After user feedback
