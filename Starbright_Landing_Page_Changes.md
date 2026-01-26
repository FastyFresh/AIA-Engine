# Starbright Landing Page - Implementation Guide

## Overview
This document contains all the changes made to the Starbright landing page for deployment on starbrightnight.com. Copy this implementation to your landing page project.

---

## Route Configuration

**Route**: `/starbright` (or root `/` depending on your setup)

---

## Complete HTML/CSS Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Starbright Night — Private Corner</title>
    <meta name="description" content="Some things aren't meant for Instagram or TikTok. Private drops + behind-the-scenes. 18+ only.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #FFF6FA;
            --card: #FFFFFF;
            --text: #1A1A1A;
            --muted: #6B5B66;
            --accent: #FF4FA3;
            --accent2: #FF7CC0;
            --border: rgba(0,0,0,0.08);
            --shadow: 0 12px 30px rgba(20, 10, 20, 0.10);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            min-height: 100vh;
            min-height: 100dvh;
            color: var(--text);
        }
        
        .container {
            max-width: 390px;
            margin: 0 auto;
            padding: 12px 20px 16px;
            min-height: 100vh;
            min-height: 100dvh;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        .brand {
            font-size: 11px;
            font-weight: 600;
            color: var(--muted);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .hero-image {
            width: 100%;
            max-width: 280px;
            aspect-ratio: 1;
            object-fit: cover;
            object-position: top center;
            border-radius: 20px;
            box-shadow: var(--shadow);
            margin-bottom: 14px;
        }
        
        .headline {
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 6px;
            line-height: 1.3;
        }
        
        .subtext {
            font-size: 14px;
            font-weight: 400;
            color: var(--muted);
            margin-bottom: 8px;
        }
        
        .social-proof {
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 12px;
        }
        
        .bullets {
            list-style: none;
            margin-bottom: 16px;
            text-align: left;
            display: inline-block;
        }
        
        .bullets li {
            font-size: 13px;
            font-weight: 500;
            color: var(--text);
            margin-bottom: 4px;
        }
        
        .cta-section {
            width: 100%;
            max-width: 320px;
        }
        
        .cta-primary {
            display: block;
            width: 100%;
            padding: 14px 24px;
            background: #1A1A1A;
            color: white;
            font-family: 'Poppins', sans-serif;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            border-radius: 14px;
            text-align: center;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
            transition: all 0.2s ease;
            margin-bottom: 6px;
        }
        
        .cta-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
        }
        
        .cta-microcopy {
            font-size: 13px;
            font-weight: 500;
            color: var(--muted);
            margin-bottom: 12px;
        }
        
        .cta-secondary {
            display: block;
            width: 100%;
            padding: 12px 24px;
            background: #FFFFFF;
            color: #1A1A1A;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            border-radius: 14px;
            text-align: center;
            border: 2px solid rgba(0, 0, 0, 0.15);
            transition: all 0.2s ease;
            margin-bottom: 4px;
        }
        
        .cta-secondary:hover {
            background: #F5F5F5;
            border-color: #1A1A1A;
        }
        
        .cta-secondary-micro {
            font-size: 12px;
            font-weight: 500;
            color: var(--muted);
            margin-bottom: 10px;
        }
        
        .reassurance {
            font-size: 10px;
            font-weight: 500;
            color: var(--muted);
            opacity: 0.8;
        }
        
        .preview-section {
            display: none;
        }
        
        @media (min-width: 768px) {
            .container {
                padding: 24px 20px;
                max-width: 480px;
            }
            
            .hero-image {
                max-width: 320px;
            }
            
            .headline {
                font-size: 24px;
            }
            
            .footer {
                margin-top: 24px;
                font-size: 11px;
                color: var(--muted);
                opacity: 0.7;
            }
            
            .footer a {
                color: var(--muted);
                text-decoration: none;
            }
        }
    </style>
    <script>
        function trackClick(eventName) {
            if (typeof gtag === 'function') {
                gtag('event', eventName);
            }
            console.log('Track:', eventName);
        }
    </script>
</head>
<body>
    <div class="container">
        <span class="brand">Starbright Night</span>
        
        <img src="/path/to/hero-image.jpg" alt="Starbright" class="hero-image">
        
        <h1 class="headline">hi!🌸 this is my private corner of the world</h1>
        
        <p class="subtext">had 64K followers on Tik Tok b4 they kicked me off 😡</p>
        
        <p class="social-proof">some things just aren't meant for TiK Tok or Insta i guess 😉</p>
        
        <ul class="bullets">
            <li>🌸 behind-the-scenes moments</li>
            <li>💖 private drops i don't post anywhere else</li>
            <li>🔔 drop alerts + little updates</li>
        </ul>
        
        <div class="cta-section">
            <a href="https://dfans.co/starbrightnight" class="cta-primary" target="_blank" onclick="trackClick('cta_dfans_click')">
                Enter My Private Space
            </a>
            <p class="cta-microcopy">full access + private drops</p>
            
            <a href="https://t.me/StarbrightMonroeBot" class="cta-secondary" target="_blank" onclick="trackClick('cta_telegram_click')">
                preview my vibe on Telegram
            </a>
            <p class="cta-secondary-micro">free previews + drop alerts</p>
        </div>
        
        <p class="reassurance">Private • Secure • Cancel anytime • 18+</p>
        
        <footer class="footer">
            © Starbright Night • 18+ | <a href="#">Privacy</a> | <a href="#">Terms</a>
        </footer>
    </div>
</body>
</html>
```

---

## Key Design Elements

### Color Scheme
- Background: `#FFF6FA` (soft pink)
- Text: `#1A1A1A` (near black)
- Muted text: `#6B5B66`
- Buttons: Black (`#1A1A1A`) with white text

### Typography
- Font: Poppins (Google Fonts)
- Weights: 400, 500, 600, 700

### Button Styling
- **Primary CTA**: Black background, white text, 14px padding, 14px border-radius
- **Secondary CTA**: White background, black text, 2px border

---

## Copy/Content

### Headlines & Text
- **Brand**: "Starbright Night"
- **Headline**: "hi!🌸 this is my private corner of the world"
- **Subtext**: "had 64K followers on Tik Tok b4 they kicked me off 😡"
- **Social proof**: "some things just aren't meant for TiK Tok or Insta i guess 😉"

### Bullet Points
- 🌸 behind-the-scenes moments
- 💖 private drops i don't post anywhere else
- 🔔 drop alerts + little updates

### CTAs
- **Primary**: "Enter My Private Space" → links to `https://dfans.co/starbrightnight`
- **Secondary**: "preview my vibe on Telegram" → links to `https://t.me/StarbrightMonroeBot`

### Reassurance Line
- "Private • Secure • Cancel anytime • 18+"

---

## Hero Image

### Requirements
- Aspect ratio: 1:1 (square)
- Max width: 280px mobile, 320px desktop
- Border radius: 20px
- Object-fit: cover
- Object-position: top center

### Cache Control (Important!)
When serving the hero image, include these headers to prevent caching issues:
```
Cache-Control: no-cache, no-store, must-revalidate
```

---

## Link Destinations

| Button | URL |
|--------|-----|
| DFANS (Primary) | https://dfans.co/starbrightnight |
| Telegram (Secondary) | https://t.me/StarbrightMonroeBot |

---

## Mobile-First Design Notes
- Container max-width: 390px on mobile
- Full viewport height (100dvh for modern browsers)
- Touch-friendly button sizing (14px+ padding)
- No horizontal scrolling

---

## Analytics Events
The page tracks two click events (if Google Analytics is configured):
- `cta_dfans_click` - Primary DFANS button
- `cta_telegram_click` - Telegram button

---

## Deployment Notes
1. Upload the hero image to your static assets
2. Update the image `src` path in the HTML
3. Ensure HTTPS is enabled
4. Test on mobile devices first
