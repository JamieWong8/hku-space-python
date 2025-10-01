# Dark Mode Implementation Guide

## Overview

Deal Scout now features a comprehensive dark mode that provides a comfortable viewing experience in low-light environments. The dark mode implementation follows best practices for accessibility and user experience.

## Features

### 1. **Automatic Theme Detection**
- Detects system theme preference on first visit
- Respects user's OS-level dark mode settings
- Automatically switches when system theme changes

### 2. **Persistent User Choice**
- Saves theme preference in localStorage
- Maintains user selection across sessions
- Override system preference with manual toggle

### 3. **Smooth Transitions**
- All color transitions are smooth and consistent
- No jarring flashes when switching themes
- Animated toggle button with rotation effect

### 4. **Comprehensive Coverage**
All UI elements support dark mode:
- ✅ Main layout and background gradients
- ✅ Cards and panels
- ✅ Tier summaries (Invest, Monitor, Avoid)
- ✅ Buttons and interactive elements
- ✅ Forms and inputs
- ✅ Tables and data displays
- ✅ Charts and visualizations
- ✅ Modals and overlays
- ✅ Navigation and headers

## Usage

### Toggle Button
- **Location**: Fixed button in bottom-right corner
- **Icon**: Moon icon (light mode) / Sun icon (dark mode)
- **Interaction**: Click to toggle between light and dark modes
- **Mobile**: Responsive sizing for smaller screens
- **Keyboard**: Fully keyboard accessible with focus indicators

### CSS Variables
The dark mode uses CSS custom properties for consistent theming:

```css
/* Light Mode (Default) */
:root {
  --surface-base: #ffffff;
  --text-primary: #1f2a44;
  --border-light: rgba(31, 42, 68, 0.08);
  /* ... more variables */
}

/* Dark Mode */
[data-theme="dark"] {
  --surface-base: #0f172a;
  --text-primary: #f8fafc;
  --border-light: rgba(255, 255, 255, 0.06);
  /* ... more variables */
}
```

## Design Decisions

### Color Adjustments
Dark mode colors are carefully calibrated for:

1. **Readability**: WCAG AA contrast ratios maintained
2. **Reduced Eye Strain**: Lower brightness, warmer tones
3. **Brand Consistency**: Brand colors adjusted for dark backgrounds
4. **Visual Hierarchy**: Depth created through subtle shadows and borders

### Tier Cards
The tier summary cards have been redesigned for dark mode compatibility:

- **Before**: Bold gradient backgrounds (hard to read in dark mode)
- **After**: Discrete bordered cards with subtle hover effects
- **Borders**: Color-coded left borders for visual identification
- **Backgrounds**: Clean white/dark backgrounds with hover highlights
- **Icons**: Semantic colors maintained (green, yellow, red)

### Component Styles

#### Light Mode Tier Cards
- White background
- Subtle colored borders
- Colored left accent bar
- Hover: Light colored background tint

#### Dark Mode Tier Cards
- Dark gray background (#1e293b)
- Same border styling
- Maintains colored accent bar
- Hover: Subtle opacity overlay

## Technical Implementation

### HTML Structure
```html
<!-- Dark Mode Toggle Button -->
<button 
    id="darkModeToggle" 
    class="dark-mode-toggle" 
    aria-label="Toggle dark mode"
    title="Toggle dark mode"
>
    <i class="fas fa-sun icon-sun"></i>
    <i class="fas fa-moon icon-moon"></i>
</button>
```

### JavaScript
```javascript
// Initialize theme on page load
const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', initialTheme);

// Toggle handler
darkModeToggle.addEventListener('click', function() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
});
```

### CSS Architecture
Dark mode styles are organized across modular CSS files:

1. **design-system.css**: Core variables and tokens
2. **components.css**: Dark mode toggle button styles
3. **home.css**: Tier cards and hero section adjustments
4. **dashboard.css**: Charts and KPIs (inherits from variables)
5. **evaluate.css**: Company cards and filters (inherits from variables)

## Browser Support

- ✅ Chrome/Edge 88+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

### Fallback Behavior
- Browsers without CSS custom property support: Light mode only
- Browsers without localStorage: Theme resets on page refresh
- No JavaScript: Light mode (can be enhanced with CSS media query)

## Accessibility

### WCAG Compliance
- ✅ Contrast ratios meet WCAG AA standards (4.5:1 for text)
- ✅ Focus indicators visible in both themes
- ✅ Color is not the only means of conveying information
- ✅ Reduced motion support respected

### Keyboard Navigation
- Toggle button: `Tab` to focus, `Enter` or `Space` to activate
- All interactive elements maintain focus visibility

### Screen Readers
- Toggle button has descriptive `aria-label`
- Icon changes announced through DOM updates
- Theme preference persists across sessions

## Customization

### Adjusting Colors
To modify dark mode colors, edit `design-system.css`:

```css
[data-theme="dark"] {
  --surface-base: #your-dark-color;
  --text-primary: #your-text-color;
  /* Add more customizations */
}
```

### Toggle Button Position
Modify position in `components.css`:

```css
.dark-mode-toggle {
  bottom: var(--spacing-6);  /* Adjust vertical position */
  right: var(--spacing-6);   /* Adjust horizontal position */
}
```

### Transition Speed
Adjust theme transition duration in `design-system.css`:

```css
body {
  transition: background var(--transition-base); /* Change to --transition-slow for slower */
}
```

## Testing

### Manual Testing Checklist
- [ ] Toggle button visible and clickable in both modes
- [ ] Theme persists after page refresh
- [ ] System theme detection works on first visit
- [ ] All tier cards readable in both modes
- [ ] Charts and graphs display correctly in dark mode
- [ ] Modals and overlays have proper contrast
- [ ] Focus indicators visible in both themes
- [ ] Mobile responsive layout works correctly

### Browser DevTools Testing
```javascript
// Test theme switching in console
document.documentElement.setAttribute('data-theme', 'dark');
document.documentElement.setAttribute('data-theme', 'light');

// Check localStorage
localStorage.getItem('theme');

// Simulate system preference change
matchMedia('(prefers-color-scheme: dark)').matches;
```

## Troubleshooting

### Theme Not Persisting
**Issue**: Theme resets to light mode on refresh
**Solution**: Check browser localStorage permissions

### Toggle Button Not Visible
**Issue**: Button hidden or missing
**Solution**: Verify CSS file loaded with correct cache-busting version (?v=2025.2)

### Colors Not Changing
**Issue**: Dark mode colors not applying
**Solution**: Check that `data-theme="dark"` attribute is on `<html>` element

### Flash of Wrong Theme
**Issue**: Brief flash of light mode before dark mode loads
**Solution**: Theme initialization script runs before DOMContentLoaded

## Future Enhancements

### Planned Features
- [ ] System theme auto-sync toggle in settings
- [ ] Multiple theme variants (high contrast, blue light filter)
- [ ] Per-component theme customization
- [ ] Theme preview before switching
- [ ] Scheduled theme switching (daytime/nighttime)
- [ ] Theme export/import for user preferences

### API Integration
Future API endpoints for theme management:
```javascript
// Save theme preference to user profile
POST /api/user/preferences
{
  "theme": "dark",
  "auto_switch": true
}
```

## Resources

### Documentation
- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [prefers-color-scheme (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
- [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

### Design System
- See `DESIGN_SYSTEM_GUIDE.md` for complete design token reference
- See `DESIGN_MODERNIZATION.md` for implementation details

## Version History

### v2025.2 - October 2025
- ✅ Added dark mode toggle button
- ✅ Implemented comprehensive dark mode styles
- ✅ Redesigned tier cards for better contrast
- ✅ Added system theme detection
- ✅ Persistent theme preference via localStorage
- ✅ Smooth transitions for all components
- ✅ Full accessibility support

---

**Last Updated**: October 2025  
**Maintained By**: Deal Scout Team  
**Related Docs**: `DESIGN_SYSTEM_GUIDE.md`, `DESIGN_MODERNIZATION.md`
