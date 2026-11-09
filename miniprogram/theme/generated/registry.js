// 由 scripts/themes/build.mjs 生成，请勿手改；修改 themes/ 后重新运行。
export const THEMES = [
  {
    "key": "neon",
    "name": "霓虹玻璃",
    "order": 1,
    "scheme": "dark",
    "swatch": [
      "#7C5CFF",
      "#22D3EE",
      "#07080F"
    ],
    "tokens": {
      "--bg": "#07080F",
      "--surface": "rgba(255,255,255,.05)",
      "--overlay": "#14152A",
      "--text": "#ECEEFA",
      "--muted": "#A3A9C2",
      "--line": "rgba(255,255,255,.08)",
      "--accent": "#7C5CFF",
      "--accent-2": "#22D3EE",
      "--accent-text": "#A996FF",
      "--on-accent": "#FFFFFF",
      "--accent-bg": "linear-gradient(135deg, #6A4CFF 0%, #2563EB 55%, #0E7490 100%)",
      "--success": "#34D399",
      "--warning": "#FBBF24",
      "--danger": "#FB7185",
      "--success-bg": "#10302B",
      "--warning-bg": "#33290F",
      "--danger-bg": "#3A1823",
      "--hero": "linear-gradient(135deg, rgba(124,92,255,.35), rgba(34,211,238,.12))",
      "--on-hero": "#ECEEFA",
      "--radius-sm": "14px",
      "--radius-md": "14px",
      "--radius-lg": "20px",
      "--radius-btn": "14px",
      "--shadow": "0 0 0 1px rgba(255,255,255,.10)",
      "--font": "\"HarmonyOS Sans SC\", \"MiSans\", \"PingFang SC\", system-ui, -apple-system, \"Microsoft YaHei\", sans-serif",
      "--mono": "\"JetBrains Mono\", \"SF Mono\", ui-monospace, Menlo, Consolas, monospace",
      "--glass": "rgba(255,255,255,.10)",
      "--glass-low-end": "#1B1C34",
      "--blur": "blur(16px)",
      "--decor": "1"
    },
    "native": {
      "tabBar": {
        "color": "#A3A9C2",
        "selectedColor": "#A996FF",
        "backgroundColor": "#0B0C16",
        "borderStyle": "white"
      },
      "navBar": {
        "frontColor": "#ffffff",
        "backgroundColor": "#07080F"
      },
      "windowBackground": "#07080F"
    }
  },
  {
    "key": "bento",
    "name": "极光 Bento",
    "order": 2,
    "scheme": "light",
    "swatch": [
      "#4F46E5",
      "#FF5C8A",
      "#F3F4FA"
    ],
    "tokens": {
      "--bg": "#F3F4FA",
      "--surface": "#FFFFFF",
      "--overlay": "#FFFFFF",
      "--text": "#11121A",
      "--muted": "#5E6378",
      "--line": "#E6E8F0",
      "--accent": "#4F46E5",
      "--accent-2": "#FF5C8A",
      "--accent-text": "#4F46E5",
      "--on-accent": "#FFFFFF",
      "--accent-bg": "#11121A",
      "--success": "#047857",
      "--warning": "#B45309",
      "--danger": "#BE123C",
      "--success-bg": "#E7F6EF",
      "--warning-bg": "#FEF3E2",
      "--danger-bg": "#FDE8EC",
      "--hero": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #DB2777 100%)",
      "--on-hero": "#FFFFFF",
      "--radius-sm": "16px",
      "--radius-md": "16px",
      "--radius-lg": "28px",
      "--radius-btn": "999px",
      "--shadow": "0 1px 2px rgba(17,18,26,.04), 0 12px 32px -12px rgba(49,46,129,.14)",
      "--font": "\"MiSans\", \"HarmonyOS Sans SC\", \"PingFang SC\", system-ui, -apple-system, \"Microsoft YaHei\", sans-serif",
      "--mono": "\"SF Mono\", \"JetBrains Mono\", ui-monospace, Menlo, Consolas, monospace",
      "--glass": "#F6F7FB",
      "--glass-low-end": "#FFFFFF",
      "--blur": "none",
      "--decor": "1"
    },
    "native": {
      "tabBar": {
        "color": "#5E6378",
        "selectedColor": "#4F46E5",
        "backgroundColor": "#F3F4FA",
        "borderStyle": "black"
      },
      "navBar": {
        "frontColor": "#000000",
        "backgroundColor": "#F3F4FA"
      },
      "windowBackground": "#F3F4FA"
    }
  },
  {
    "key": "terminal",
    "name": "赛博终端",
    "order": 3,
    "scheme": "dark",
    "swatch": [
      "#C6FF3D",
      "#FF3DBB",
      "#0A0A0B"
    ],
    "tokens": {
      "--bg": "#0A0A0B",
      "--surface": "#111113",
      "--overlay": "#111113",
      "--text": "#F2F2F0",
      "--muted": "#9A9A94",
      "--line": "#26262A",
      "--accent": "#C6FF3D",
      "--accent-2": "#FF3DBB",
      "--accent-text": "#C6FF3D",
      "--on-accent": "#0A0A0B",
      "--accent-bg": "#C6FF3D",
      "--success": "#C6FF3D",
      "--warning": "#FFC53D",
      "--danger": "#FF5A5A",
      "--success-bg": "#1B2410",
      "--warning-bg": "#2B2208",
      "--danger-bg": "#2E1111",
      "--hero": "#111113",
      "--on-hero": "#F2F2F0",
      "--radius-sm": "4px",
      "--radius-md": "4px",
      "--radius-lg": "4px",
      "--radius-btn": "2px",
      "--shadow": "none",
      "--font": "\"HarmonyOS Sans SC\", \"PingFang SC\", system-ui, -apple-system, \"Microsoft YaHei\", sans-serif",
      "--mono": "\"JetBrains Mono\", \"SF Mono\", ui-monospace, Menlo, Consolas, monospace",
      "--glass": "#1C1C1F",
      "--glass-low-end": "#111113",
      "--blur": "none",
      "--decor": "1"
    },
    "native": {
      "tabBar": {
        "color": "#9A9A94",
        "selectedColor": "#C6FF3D",
        "backgroundColor": "#0A0A0B",
        "borderStyle": "white"
      },
      "navBar": {
        "frontColor": "#ffffff",
        "backgroundColor": "#0A0A0B"
      },
      "windowBackground": "#0A0A0B"
    }
  }
]
export const DEFAULT_THEME = 'bento'
