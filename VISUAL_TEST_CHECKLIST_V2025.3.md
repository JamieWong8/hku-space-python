# Quick Visual Test Checklist - v2025.3

## 🎯 Critical Fixes to Verify

### 1. Tier Cards (Home Tab)
Open http://localhost:5000 → Home tab

#### ✅ Monitor Card Text Layout
- [ ] Text "Promising—watch closely" is **fully visible** (not cut off)
- [ ] No horizontal overflow
- [ ] Min height looks comfortable (160px)
- [ ] Text wraps nicely on smaller screens

**How to Test**: 
- Resize browser window to different widths
- Check Monitor card specifically (was the problem card)
- Verify all three cards have consistent heights

---

### 2. Hero Text Visibility (Home Tab)
Scroll to top of Home tab

#### ✅ Light Mode (Default)
- [ ] "AI-Powered Deal Evaluation" title is **WHITE and READABLE**
- [ ] Subtitle text is **WHITE and READABLE**
- [ ] Hero icon labels are **WHITE**

#### ✅ Dark Mode
Click toggle button (bottom-right) to switch to dark mode:
- [ ] "AI-Powered Deal Evaluation" title is **STILL WHITE** (not dark gray)
- [ ] Subtitle text is **STILL WHITE**
- [ ] Hero icons labels are **STILL WHITE**

**Expected**: Hero text should be white in BOTH light and dark modes

---

### 3. Score Badges (Evaluate Companies Tab)
Click "Evaluate Companies" tab → View company cards

#### ✅ Light Mode
Click toggle to switch to LIGHT mode:
- [ ] Invest badges: Light green background, dark green text ✅
- [ ] Monitor badges: Light yellow background, dark yellow text ✅
- [ ] Avoid badges: Light red background, dark red text ✅
- [ ] Score badges: Light gray background, dark text ✅

#### ✅ Dark Mode
Click toggle to switch to DARK mode:
- [ ] Invest badges: Dark green background (20% opacity), **LIGHT GREEN TEXT** ✅
- [ ] Monitor badges: Dark yellow background (20% opacity), **LIGHT YELLOW TEXT** ✅
- [ ] Avoid badges: Dark red background (20% opacity), **LIGHT RED TEXT** ✅
- [ ] Score badges: Dark gray background, **LIGHT GRAY TEXT** ✅

**Key Test**: In dark mode, badge text should be LIGHT colored (not dark)

---

### 4. Analysis Modal (Click Analyze on Any Company)
Click any "Analyze" button to open the analysis modal

#### ✅ Light Mode
Switch to LIGHT mode, open modal:
- [ ] Modal background: WHITE ✅
- [ ] KPI cards: WHITE with subtle border ✅
- [ ] Chart cards: WHITE ✅
- [ ] Tables: WHITE with light striping ✅

#### ✅ Dark Mode
Switch to DARK mode, open modal:
- [ ] Modal background: **DARK GRAY** (not white) ✅
- [ ] Modal header: **DARK GRAY** with darker stripe ✅
- [ ] KPI cards: **DARK GRAY** background ✅
- [ ] Chart cards: **DARK GRAY** background ✅
- [ ] Chart card headers: **DARKER GRAY** ✅
- [ ] Tables: **DARK** with subtle striping ✅
- [ ] Active tab: **BLUE** background with white text ✅
- [ ] Close button (X): **WHITE** (inverted) ✅
- [ ] All text: **LIGHT COLORED** and readable ✅

**Key Test**: In dark mode, modal should have NO white backgrounds

---

### 5. Dark Mode Toggle Button (Bottom-Right Corner)
Look at bottom-right corner of page

#### ✅ Visibility
- [ ] Toggle button is **VISIBLE** and **PROMINENT**
- [ ] Has glassmorphic blur effect (slightly transparent)
- [ ] Shows moon icon (🌙) in LIGHT mode
- [ ] Shows sun icon (☀️) in DARK mode
- [ ] Desktop: 56px × 56px
- [ ] Mobile: 52px × 52px

#### ✅ Interactions
- [ ] **Hover**: Button scales up (1.1x) and shows themed shadow
  - Light mode hover: Blue tint
  - Dark mode hover: Yellow tint
- [ ] **Click**: Switches theme immediately (no rotation, just scale)
- [ ] **Focus** (Tab key): Shows blue outline
- [ ] **Keyboard** (Enter/Space): Activates toggle

---

## 🔄 Theme Switching Test

### Quick Switch Test
1. Start in light mode (default)
2. Click toggle → Should switch to dark mode
3. Click toggle → Should switch back to light mode
4. Click toggle 10 times rapidly → Should work every time
5. Refresh page (F5) → Should remember last theme

### Persistence Test
1. Switch to dark mode
2. Refresh page (F5)
3. **Expected**: Page loads in dark mode (no flash of light theme)
4. Check localStorage: `localStorage.getItem('theme')` should be `"dark"`

### System Theme Test
1. Clear localStorage: `localStorage.clear()`
2. Set OS to dark mode
3. Refresh page
4. **Expected**: Page loads in dark mode (auto-detected)

---

## 🎨 Color Contrast Spot Checks

### Dark Mode Contrast
Open DevTools → Elements → Computed styles

Check these elements in DARK mode:

| Element | Background | Text Color | Contrast Ratio |
|---------|-----------|------------|----------------|
| Modal header | #1e293b | #f8fafc | > 12:1 ✅ |
| KPI value (Invest) | #1e293b | #34d399 | > 5:1 ✅ |
| Badge (Monitor) | rgba(246,192,0,0.2) | #fcd34d | > 8:1 ✅ |
| Table text | #1e293b | #cbd5e1 | > 7:1 ✅ |

**All should meet WCAG AA (4.5:1) or better**

---

## 📱 Mobile Responsive Test

### Desktop (>1200px)
- [ ] Tier cards: 3 columns side-by-side
- [ ] Toggle button: 56px, bottom-right
- [ ] Modal: Full width with padding

### Tablet (768px - 992px)
- [ ] Tier cards: Stack vertically
- [ ] Toggle button: 52px, bottom-right
- [ ] Modal: Full width

### Mobile (<768px)
- [ ] Tier cards: Full width, stacked
- [ ] Toggle button: 52px, bottom-right (smaller)
- [ ] Modal: Full screen with minimal padding
- [ ] All text readable at mobile sizes

---

## ⚡ Performance Check

### Page Load
Open DevTools → Network → Hard Refresh (Ctrl+F5):
- [ ] CSS files load with `?v=2025.3` query parameter
- [ ] All CSS files load in <200ms
- [ ] No 404 errors
- [ ] Total CSS size: ~60KB (acceptable)

### Theme Switch
Open DevTools → Performance → Record:
1. Click toggle button
2. Stop recording
3. Check flame chart:
   - [ ] Theme switch completes in <10ms
   - [ ] No layout shift (reflow)
   - [ ] Only repaint events (color changes)

---

## 🐛 Bug Checks

### Common Issues to Verify Fixed

#### Issue 1: Tier Card Overflow
- [x] Monitor card shows full text "Promising—watch closely"
- [x] No "..." truncation
- [x] No horizontal scroll

#### Issue 2: Hero Text Invisible
- [x] Hero title visible in dark mode
- [x] Hero subtitle visible in dark mode
- [x] Text is white, not dark gray

#### Issue 3: Badge Contrast
- [x] Invest badge readable in dark mode (light green text)
- [x] Monitor badge readable in dark mode (light yellow text)
- [x] Avoid badge readable in dark mode (light red text)

#### Issue 4: Modal White Backgrounds
- [x] No white backgrounds in modal when in dark mode
- [x] All card backgrounds dark gray
- [x] Close button visible (white X)

#### Issue 5: Toggle Visibility
- [x] Toggle button prominent and visible
- [x] Glassmorphic effect visible
- [x] Hover effect shows themed colors

---

## ✅ Sign-Off Checklist

Before considering testing complete:

### Visual
- [ ] All tier cards display correctly
- [ ] Hero text visible in both modes
- [ ] All badges readable in both modes
- [ ] Modal fully dark mode compatible
- [ ] Toggle button visible and functional

### Functional
- [ ] Theme toggle switches correctly
- [ ] Theme persists after refresh
- [ ] System theme detection works
- [ ] No console errors
- [ ] No 404 errors for CSS files

### Accessibility
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader announces toggle

### Performance
- [ ] Page loads quickly (<2s)
- [ ] Theme switches instantly (<10ms)
- [ ] No layout shift
- [ ] No memory leaks

---

## 🎉 Success Criteria

**All tests passed = Ready for production**

If any test fails:
1. Note the specific failure
2. Check browser console for errors
3. Verify CSS version is 2025.3
4. Hard refresh browser (Ctrl+F5)
5. If still failing, report bug with details

---

## 📸 Screenshot Checklist

Take screenshots for documentation:

1. **Home Tab - Light Mode**
   - [ ] Full page view
   - [ ] Tier cards close-up
   - [ ] Hero section

2. **Home Tab - Dark Mode**
   - [ ] Full page view showing dark theme
   - [ ] Tier cards in dark mode
   - [ ] Toggle button visible

3. **Evaluate Tab - Dark Mode**
   - [ ] Company cards with badges
   - [ ] Close-up of badges showing colors

4. **Analysis Modal - Dark Mode**
   - [ ] KPI cards section
   - [ ] Chart cards
   - [ ] Panel with table
   - [ ] Active tab state

5. **Toggle Button**
   - [ ] Light mode (moon icon)
   - [ ] Dark mode (sun icon)
   - [ ] Hover state

---

## 🔄 Final Verification

Run this in browser console:

```javascript
// Quick verification script
console.log('=== Dark Mode Test Suite ===');

// 1. Check theme system
const theme = document.documentElement.getAttribute('data-theme');
console.log('✓ Current theme:', theme);

// 2. Check localStorage
const saved = localStorage.getItem('theme');
console.log('✓ Saved theme:', saved);

// 3. Check toggle button
const toggle = document.getElementById('darkModeToggle');
console.log('✓ Toggle button exists:', !!toggle);

// 4. Check CSS variables
const root = document.documentElement;
const surfaceBase = getComputedStyle(root).getPropertyValue('--surface-base');
console.log('✓ Surface base color:', surfaceBase);

// 5. Check CSS version
const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
const versions = Array.from(cssLinks).map(link => {
  const match = link.href.match(/v=([0-9.]+)/);
  return match ? match[1] : 'unknown';
});
console.log('✓ CSS versions:', versions);

console.log('=== Test Complete ===');
```

**Expected Output**:
```
=== Dark Mode Test Suite ===
✓ Current theme: light (or dark)
✓ Saved theme: light (or dark, or null)
✓ Toggle button exists: true
✓ Surface base color: #ffffff (or #0f172a in dark mode)
✓ CSS versions: ["2025.3", "2025.3", "2025.3", "2025.3", "2025.3"]
=== Test Complete ===
```

---

**Testing Status**: ⏳ Ready to Test  
**Estimated Time**: 10-15 minutes  
**Last Updated**: October 2025
