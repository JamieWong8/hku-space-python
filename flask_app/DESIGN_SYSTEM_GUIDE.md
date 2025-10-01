# Deal Scout Design System Guide

## Overview
This document describes the comprehensive design system implemented for Deal Scout, providing a modern, accessible, and maintainable visual foundation.

## Architecture

### CSS Structure
The design system follows a modular architecture with clear separation of concerns:

1. **design-system.css** - Core variables, tokens, and utilities
2. **components.css** - Reusable UI components (cards, buttons, forms, badges)
3. **dashboard.css** - Analysis modal, charts, and KPIs
4. **evaluate.css** - Company cards, filters, and pagination
5. **home.css** - Hero section, features, and landing page

### Load Order
```html
<!-- 1. Design System Foundation -->
<link rel="stylesheet" href="css/design-system.css">

<!-- 2. Component Library -->
<link rel="stylesheet" href="css/components.css">

<!-- 3. Feature-Specific Modules -->
<link rel="stylesheet" href="css/dashboard.css">
<link rel="stylesheet" href="css/evaluate.css">
<link rel="stylesheet" href="css/home.css">
```

## Design Tokens

### Color System

#### Brand Colors
```css
--brand-navy: #1f2a44      /* Primary brand color */
--brand-blue: #2f80ed      /* Interactive elements */
--brand-teal: #10b981      /* Success/positive actions */
--brand-gold: #f6c000      /* Warnings/monitoring */
--brand-red: #e74c3c       /* Errors/avoid actions */
```

#### Semantic Colors
- **Primary**: Used for main actions, links, and interactive elements
- **Success**: Positive feedback, "Invest" tier
- **Warning**: Cautionary feedback, "Monitor" tier  
- **Danger**: Negative feedback, "Avoid" tier
- **Info**: Informational messages

#### Neutral Palette
11-step gray scale from `--neutral-50` (lightest) to `--neutral-900` (darkest)

### Typography

#### Font Family
- **Base**: Inter, system UI fallbacks
- **Display**: Inter (display font)
- **Monospace**: JetBrains Mono, Fira Code, Consolas

#### Font Sizes
Fluid scale from `--font-size-xs` (12px) to `--font-size-5xl` (48px)

#### Font Weights
- Normal: 400
- Medium: 500
- Semibold: 600
- Bold: 700
- Extrabold: 800

### Spacing Scale
Based on 4px grid system:
- `--spacing-1` through `--spacing-20`
- From 4px to 80px in incremental steps

### Border Radius
```css
--radius-sm: 8px
--radius-md: 12px
--radius-lg: 16px
--radius-xl: 20px
--radius-full: 9999px
```

### Shadow System
6-level elevation system from `--shadow-xs` to `--shadow-2xl`

### Transitions
```css
--transition-fast: 150ms
--transition-base: 250ms
--transition-slow: 350ms
--transition-spring: 500ms (with bounce easing)
```

## Component Patterns

### Cards

#### Default Card
```html
<div class="card">
  <div class="card-header">Header</div>
  <div class="card-body">Content</div>
  <div class="card-footer">Footer</div>
</div>
```

#### Card Variants
- `.card-glass` - Glassmorphic with backdrop blur
- `.card-neomorph` - Neumorphic with soft shadows
- `.card-elevated` - Stronger elevation
- `.card-interactive` - Adds cursor and focus states

### Buttons

#### Primary Button
```html
<button class="btn btn-primary">Primary Action</button>
```

#### Button Variants
- `.btn-primary` - Main call-to-action
- `.btn-secondary` - Secondary actions
- `.btn-success` - Positive actions
- `.btn-warning` - Cautionary actions
- `.btn-danger` - Destructive actions
- `.btn-ghost` - Transparent background
- `.btn-outline` - Outline style

#### Button Sizes
- `.btn-xs` - Extra small
- `.btn-sm` - Small
- (default) - Medium
- `.btn-lg` - Large
- `.btn-xl` - Extra large

### Badges

```html
<span class="badge badge-primary">Label</span>
```

Badge variants: `badge-primary`, `badge-success`, `badge-warning`, `badge-danger`, `badge-info`, `badge-neutral`

### Forms

```html
<div class="form-group">
  <label class="form-label">Field Label</label>
  <input type="text" class="form-control" placeholder="Placeholder">
  <div class="form-text">Helper text</div>
</div>
```

#### Form States
- `.is-valid` - Success state
- `.is-invalid` - Error state
- `:disabled` - Disabled state

### Tabs

```html
<ul class="nav nav-pills">
  <li class="nav-item">
    <button class="nav-link active">Tab 1</button>
  </li>
  <li class="nav-item">
    <button class="nav-link">Tab 2</button>
  </li>
</ul>
```

## Dark Mode

### Implementation
Dark mode is prepared via `[data-theme="dark"]` attribute selector:

```javascript
// Toggle dark mode
document.documentElement.setAttribute('data-theme', 'dark');

// Remove dark mode
document.documentElement.removeAttribute('data-theme');
```

### Dark Mode Variables
All color variables automatically adjust when dark mode is active. Key changes:
- Surface colors become dark
- Text colors invert
- Borders become lighter
- Shadows become more pronounced

## Accessibility

### Focus States
All interactive elements have visible focus indicators:
```css
.focus-ring:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Color Contrast
All text and interactive elements meet WCAG AA standards (4.5:1 minimum contrast ratio).

### Screen Reader Support
- Semantic HTML
- ARIA labels where needed
- `.sr-only` utility class for screen reader-only content

### Keyboard Navigation
- Logical tab order
- Focus visible indicators
- Skip links for main content

## Animation Guidelines

### Entrance Animations
```html
<div class="reveal-up">Content fades in and slides up</div>
```

Apply `.reveal-in` class when element enters viewport.

### Reduced Motion
All animations respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Responsive Breakpoints

Mobile-first approach with the following breakpoints:
- **sm**: 576px
- **md**: 768px
- **lg**: 992px
- **xl**: 1200px
- **2xl**: 1400px

## Best Practices

### 1. Use Design Tokens
Always reference CSS variables instead of hardcoded values:
```css
/* Good */
color: var(--text-primary);
padding: var(--spacing-4);

/* Avoid */
color: #1f2a44;
padding: 16px;
```

### 2. Semantic Class Names
Use semantic, descriptive class names:
```css
/* Good */
.card-interactive
.btn-primary
.text-danger

/* Avoid */
.blue-button
.big-text
.box-1
```

### 3. Component Composition
Build complex components by composing simpler ones:
```html
<div class="card card-elevated">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
  </div>
  <div class="card-body">
    <p class="text-secondary">Description</p>
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

### 4. Consistent Spacing
Use the spacing scale consistently:
```css
.component {
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-6);
  gap: var(--spacing-3);
}
```

### 5. Progressive Enhancement
Build for accessibility first, enhance with modern features:
```css
/* Base styles for all browsers */
.card {
  background: var(--surface-base);
  border: 1px solid var(--border-light);
}

/* Enhanced for modern browsers */
@supports (backdrop-filter: blur(10px)) {
  .card-glass {
    backdrop-filter: blur(10px);
  }
}
```

## Future Enhancements

### Planned Features
1. Dark mode toggle UI component
2. Theme customizer
3. Extended color palette options
4. Additional component variants
5. Animation library expansion

### Maintenance
- Version all CSS files with query parameters
- Document breaking changes
- Maintain backward compatibility where possible
- Test across browsers and devices

## Resources

### Tools
- **Inter Font**: Google Fonts
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization

### Testing
- Chrome DevTools
- Firefox Developer Tools
- Axe DevTools (accessibility)
- Lighthouse (performance & accessibility)

---

**Version**: 2025.1  
**Last Updated**: October 2025  
**Maintainer**: Deal Scout Development Team
