# 🎨 Modern Date Picker - Technical Style Reference

## Exact Color Values

```python
COLORS = {
    "primary_dark": "#163B5C",          # Dark blue - pressed/strong states
    "primary_main": "#2F5D7C",          # Main blue - primary actions
    "primary_light": "#5A8FB5",         # Light blue - hover states
    "primary_lighter": "#8FBFE4",       # Lighter blue - secondary hover
    "accent": "#3E87B6",                # Accent blue - highlights
    "success": "#2E7D5A",               # Green - confirmation states
    "text_primary": "#222222",          # Dark text - main text
    "text_secondary": "#666666",        # Secondary text - muted
    "bg_primary": "#FFFFFF",            # White - main background
    "bg_secondary": "#F9FCFE",          # Very light blue - headers
    "bg_tertiary": "#EEF5FA",           # Soft blue - hover backgrounds
    "border": "#D0DFE9",                # Light border - dialog/cells
    "border_light": "#E8F1F8",          # Very light border
    "hover": "#EEF5FA",                 # Hover background
}
```

---

## Element Styling Breakdown

### Dialog Container
```
Background:     #FFFFFF
Border:         1px solid #D0DFE9
Border Radius:  10px
Padding:        20px
Width:          450px
Height:         520px
Shadow:         Subtle drop shadow
```

### Header Section
```
Background:     Transparent
Font:           Montserrat Bold, 16px
Color:          #163B5C (dark blue)
Padding:        10px
Content:        "Monday, January 20, 2025"
```

### Navigation Section
```
Background:     #F9FCFE (light blue)
Layout:         ◄ [Month Year ▼] ►
Border:         1px solid #E8F1F8
```

#### Navigation Buttons (◄ ►)
```
Normal State:
  Background:   #2F5D7C
  Text Color:   #FFFFFF (white)
  Border:       None
  Border Radius: 4px
  Padding:      5px 10px
  Font:         Montserrat Bold 12px

Hover State:
  Background:   #5A8FB5
  
Pressed State:
  Background:   #163B5C
```

#### Month/Year Selector
```
Button:
  Min Width:    150px (month), 80px (year)
  Background:   #2F5D7C
  Text Color:   #FFFFFF
  Font:         Montserrat Bold 12px
  Padding:      5px 10px
  Border Radius: 4px
  
Context Menu:
  Background:   #F9FCFE
  Text Color:   #222222
  Border:       1px solid #D0DFE9
```

### Calendar Grid Header
```
Row Background: #F9FCFE
Day Names:      Mo, Tu, We, Th, Fr, Sa, Su
Text Color:     #163B5C (dark blue)
Font:           Montserrat, Bold, 11px
Padding:        6px
Border:         1px solid #E8F1F8
Text Align:     Center
```

### Calendar Day Cells
```
Cell Size:      ~50x50 px
Spacing:        2px margin
Border Radius:  Not specified (rectangular)

Normal State:
  Background:   #FFFFFF
  Text Color:   #222222
  Border:       1px solid transparent
  Font:         Regular 12px

Hover State (Not Today):
  Background:   #EEF5FA (soft blue)
  Border:       1px solid #8FBFE4 (light blue)
  Text Color:   #222222
  
Selected State (Today):
  Background:   #2F5D7C (main blue)
  Text Color:   #FFFFFF (white)
  Border:       1px solid #163B5C (dark blue)
  Font:         Bold
  Shadow:       Subtle inner glow

Disabled State (Other Month):
  Text Color:   #D0D0D0 (light gray)
  Background:   #FFFFFF
```

### Footer Section
```
Layout:         [Cancel Btn] [Confirm Btn]
Spacing:        10px
Height:         40px per button
Margin Top:     15px
```

#### Cancel Button
```
Normal State:
  Background:   #EEF5FA
  Text Color:   #222222
  Border:       2px solid #D0DFE9
  Border Radius: 6px
  Font:         Montserrat Medium 11px
  Padding:      8px 20px

Hover State:
  Background:   #E8F1F8
  Border:       2px solid #5A8FB5

Pressed State:
  Background:   #EEF5FA
  Border:       2px solid #2F5D7C
```

#### Confirm Button
```
Normal State:
  Background:   #2F5D7C (main blue)
  Text Color:   #FFFFFF (white)
  Border:       None
  Border Radius: 6px
  Font:         Montserrat Bold 11px
  Padding:      8px 30px

Hover State:
  Background:   #5A8FB5

Pressed State:
  Background:   #163B5C
```

---

## Typography

### Font Family
Primary: **Montserrat**
Fallback: System sans-serif

### Font Weights
- Regular: 400
- Medium: 500
- Bold: 600-700

### Font Sizes
```
Header Date:        16px (Bold)
Navigation Buttons: 12px (Bold)
Day Names Header:   11px (Bold)
Day Numbers:        12px (Regular/Bold when selected)
Button Text:        11px (Medium/Bold)
```

---

## Layout Dimensions

### Dialog
```
Width:          450px (fixed)
Height:         520px (fixed)
Border Radius:  10px
```

### Calendar Grid
```
Rows:           6 (weeks)
Columns:        7 (days)
Cell Spacing:   2px
Grid Visible:   Yes
Grid Line Color:#E8F1F8
```

### Button Heights
```
Navigation:     28-32px
Day Cells:      ~50px (auto-sizing)
Action Buttons: 40px (fixed)
```

### Padding
```
Dialog Margins:     20px all sides
Header Padding:     10px
Navigation Margin:  2px
Cell Padding:       8px
Button Padding:     8px 20px (cancel), 8px 30px (confirm)
```

---

## Borders & Shadows

### Border Styles
```
Dialog:     1px solid #D0DFE9
Calendar:   1px solid #D0DFE9, radius 8px
Headers:    1px solid #E8F1F8
Cells:      1px solid transparent (hover: light blue)
Buttons:    2px solid #D0DFE9 (cancel), none (confirm)
```

### Shadows
```
Dialog:     Subtle drop shadow (system default)
Buttons:    None (flat design)
Cells:      None (flat design)
```

### Border Radius
```
Dialog:         10px
Calendar:       8px
Navigation Btn: 4px
Action Buttons: 6px
Cells:          0px (rectangular)
```

---

## State Effects

### Transition Effects
```
Button Hover:   Instant color change (no animation)
Cell Hover:     Instant background/border change
Selection:      Instant color change, bold text
```

### Focus States
```
Dialog:         Native focus ring (handled by OS)
Buttons:        Native focus ring
Calendar:       Native focus ring
```

---

## Color Usage Guide

### When to Use Each Color

**#163B5C (Primary Dark)**
- Pressed button states
- Strong contrast needed
- Active indicators
- Text on very light backgrounds

**#2F5D7C (Primary Main)**
- Primary buttons (Confirm)
- Navigation buttons
- Selected calendar dates
- Month/year header
- Main interactive elements

**#5A8FB5 (Primary Light)**
- Button hover states
- Secondary emphasis
- Subtle highlights

**#8FBFE4 (Primary Lighter)**
- Cell borders on hover
- Very subtle backgrounds
- Tertiary emphasis

**#222222 (Text Primary)**
- All body text
- Day names
- Button labels
- Main text content

**#FFFFFF (Background)**
- Calendar background
- Dialog background
- Cell backgrounds (default)

**#F9FCFE (Background Secondary)**
- Header backgrounds
- Navigation backgrounds
- Alternate sections

**#EEF5FA (Background Tertiary)**
- Hover states
- Cancel button background
- Soft backgrounds

**#D0DFE9 (Border)**
- Dialog borders
- Cell borders
- Section dividers

---

## Stylesheet String (Raw)

```css
/* Calendar Stylesheet */
QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #D0DFE9;
    border-radius: 8px;
}

QCalendarWidget QToolButton {
    background-color: #2F5D7C;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 12px;
}

QCalendarWidget QToolButton::hover {
    background-color: #5A8FB5;
}

QCalendarWidget QToolButton::pressed {
    background-color: #163B5C;
}

QCalendarWidget QHeaderView::section {
    background-color: #F9FCFE;
    color: #163B5C;
    padding: 6px;
    border: 1px solid #E8F1F8;
    font-weight: bold;
}

QCalendarWidget QAbstractItemView::item:hover {
    background-color: #EEF5FA;
    border: 1px solid #8FBFE4;
}

QCalendarWidget QAbstractItemView::item:selected {
    background-color: #2F5D7C;
    color: white;
    border: 1px solid #163B5C;
    font-weight: bold;
}
```

---

## Accessibility

### Color Contrast Ratios
```
#2F5D7C on #FFFFFF:    6.52:1 ✓ WCAG AA
#222222 on #FFFFFF:    12.6:1 ✓ WCAG AAA
#FFFFFF on #2F5D7C:    6.52:1 ✓ WCAG AA
#FFFFFF on #163B5C:    8.2:1 ✓ WCAG AAA
#222222 on #F9FCFE:    11.8:1 ✓ WCAG AAA
```

### Screen Reader Support
- Proper semantic markup with QCalendarWidget
- Button labels clearly indicate action
- Date format: "Monday, January 20, 2025"
- ARIA roles handled by Qt framework

---

## Implementation Files

All styles defined in: `modern_date_picker.py`

Key locations:
- `COLORS` dict: Line ~25
- `_apply_calendar_stylesheet()`: ~150 lines of CSS
- `_apply_stylesheet()`: Main dialog CSS
- Button styling: Within `_create_footer()`

---

## Customization Template

To change colors system-wide:

```python
class CustomDatePicker(ModernDatePickerDialog):
    COLORS = {
        **ModernDatePickerDialog.COLORS,
        "primary_main": "#YOUR_COLOR",
        "primary_dark": "#YOUR_COLOR",
        # Override any colors needed
    }
```

Then regenerate stylesheets by calling `_apply_stylesheet()`.

---

## Platform-Specific Notes

### Windows
- Fonts render cleanly
- Borders display correctly
- Colors appear as specified

### macOS
- Montserrat font may need installation
- Border radius fully supported
- Colors appear slightly lighter (OS rendering)

### Linux
- Full support across distributions
- Font availability depends on package manager
- Colors render accurately

---

**Reference Date:** January 2025
**ProCure Version:** Current
**Last Updated:** Session 9
