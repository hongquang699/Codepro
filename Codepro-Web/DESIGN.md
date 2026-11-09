---
name: CodeProOJ
description: Hải đồ & bảng thủy triều. Nền xanh hải đồ nhạt, mực xanh đậm, số tabular, một màu cảnh báo duy nhất cho dòng vừa đổi hạng.
colors:
  primary: "#0a5c8f"
  primary-hover: "#08486f"
  primary-active: "#063a5a"
  accent: "#0e7490"
  alert: "#d4520a"
  success: "#16734a"
  danger: "#b4232d"
  warning: "#a35a00"
  info: "#0a6d9c"
  on-primary: "#ffffff"
  chart-paper: "#eef3f5"
  chart-paper-deep: "#e3ecef"
  surface: "#fbfdfd"
  surface-hover: "#f0f6f7"
  isobath: "#c6d5db"
  isobath-subtle: "#dbe6ea"
  table-header: "#e1ebee"
  input-border: "#9fb3bd"
  ink: "#0b2236"
  ink-secondary: "#2c4558"
  ink-muted: "#4d6678"
  ink-dim: "#587181"
typography:
  display:
    fontFamily: "Be Vietnam Pro, Inter, sans-serif"
    fontSize: "clamp(2.2rem, 5.4vw, 4.4rem)"
    lineHeight: 1.08
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Be Vietnam Pro, Inter, sans-serif"
    fontSize: "clamp(1.65rem, 2.6vw, 2.5rem)"
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  stat:
    fontFamily: "Be Vietnam Pro, Inter, sans-serif"
    fontSize: "2.2rem"
    fontWeight: 800
    letterSpacing: "-0.04em"
    fontFeature: "tnum"
  body:
    fontFamily: "Be Vietnam Pro, Inter, sans-serif"
    fontSize: "1rem"
    lineHeight: 1.6
  label:
    fontFamily: "Be Vietnam Pro, Inter, sans-serif"
    fontSize: "0.75rem"
    letterSpacing: "0.06em"
  mono:
    fontFamily: "JetBrains Mono, ui-monospace, Consolas, monospace"
    fontSize: "0.875rem"
rounded:
  sm: "3px"
  md: "5px"
  lg: "8px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    height: "42px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.md}"
    height: "42px"
  input:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "42px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
  badge:
    rounded: "{rounded.sm}"
  table-header:
    backgroundColor: "{colors.table-header}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
  scoreboard-row-changed:
    textColor: "{colors.ink}"
---

# Design System: CodeProOJ

## Overview

**Creative North Star: "Hải đồ & bảng thủy triều"**

Mỗi bài là một điểm trên hải đồ, thứ hạng là dòng nước đang dâng. Giao diện là một công cụ làm việc: nền xanh hải đồ nhạt, mực xanh đậm, đường kẻ mảnh như đường đẳng sâu, số căn theo giá trị vị trí. Sáng là mặc định, tối ("hải đồ ban đêm") ngang hàng; mọi thành phần đổi theme chỉ qua token màu.

Hệ thống phẳng và dày thông tin. Độ sâu đến từ tông nền và viền mảnh, không từ bóng đổ hay gradient. Chuyển động chỉ phục vụ nghĩa: dòng đổi hạng trượt tại chỗ (FLIP, 420ms) và giữ màu cảnh báo cho đến khi người dùng nhận ra.

Nguồn token duy nhất: `frontend/css/global/site-refresh.css` (nạp cuối trên mọi trang, ghi đè `variables.css` và khối cùng tên trong `theme.css`).

**Key Characteristics:**
- Một nền xanh hải đồ, một màu nhấn xanh biển, một màu cảnh báo cam cháy dành riêng cho thay đổi hạng.
- Số tabular ở mọi bảng, điểm, hạng, thời gian.
- Bán kính nhỏ 3/5/8px, góc gần vuông như khung bản đồ.
- Phẳng: bóng chỉ là sợi mảnh hoặc nhẹ; không glow, không nâng khi hover.
- Sáng mặc định, tối ngang hàng.

## Colors

Bảng màu hải đồ: nền xanh xám nhạt, mực xanh đêm, một xanh biển cho hành động, một cam cho cảnh báo. Giá trị trong frontmatter là chế độ sáng (mặc định); chế độ tối nằm trong sidecar `.impeccable/design.json` (`colorMeta.*.dark`) và khối `[data-theme="dark"]` của `site-refresh.css`.

### Primary
- **Xanh biển hải đồ** (`primary` #0a5c8f; hover #08486f; active #063a5a): nút chính, liên kết, tab đang chọn, tên thí sinh, viền focus (vòng `--ui-ring` 3px, 28% alpha). Chữ trên nền này luôn dùng `on-primary` (#ffffff sáng, #04202f tối).

### Secondary
- **Lam ngọc** (`accent` #0e7490): nhấn phụ, hiếm dùng.

### Tertiary (tín hiệu)
- **Cam cảnh báo** (`alert` #d4520a; tối #ff8a3d): chỉ dành cho dòng vừa đổi hạng. Nền `--color-alert-bg`, vạch trái 3px.
- **Lục, đỏ, hổ phách, lam thông tin** (`success` #16734a, `danger` #b4232d, `warning` #a35a00, `info` #0a6d9c): trạng thái chấm bài (AC, WA, TLE) và thông báo. Mỗi màu có nền `-bg` alpha 11-12%.

### Neutral
- **Giấy hải đồ** (`chart-paper` #eef3f5, `chart-paper-deep` #e3ecef): nền trang và nền phụ, sidebar, code.
- **Mặt giấy** (`surface` #fbfdfd, hover #f0f6f7): thẻ, bảng, modal.
- **Đường đẳng sâu** (`isobath` #c6d5db, `isobath-subtle` #dbe6ea): viền thẻ, đường kẻ bảng. Đầu bảng #e1ebee. Viền ô nhập #9fb3bd.
- **Mực** (`ink` #0b2236, `ink-secondary` #2c4558, `ink-muted` #4d6678, `ink-dim` #587181): bốn bậc chữ.

### Named Rules
**The One Alert Rule.** `--color-alert` chỉ xuất hiện trên dòng bảng điểm có `.rank-changed`. Không dùng cho lỗi (đó là `danger`), cảnh báo chung (`warning`) hay trang trí.

**The Token Only Rule.** Mọi màu đi qua custom property để sáng và tối cùng đổi. Màu cứng trong CSS từng trang là khoảng trống đã biết, không phải quy tắc.

## Typography

**Display / Body:** Be Vietnam Pro (fallback Inter, sans-serif), tự lưu trong `fonts.css`, đủ dấu tiếng Việt.
**Mono:** JetBrains Mono, cho mã và khối `pre`.

**Character:** Một họ chữ không chân đậm, tiêu đề siết chặt (tracking âm), nhãn bảng nhỏ in hoa kiểu chú giải hải đồ.

### Hierarchy
- **Display** (clamp 2.2-4.4rem, lh 1.08, tracking -0.045em): tiêu đề hero trang chủ; 2.1rem dưới 600px.
- **Headline** (clamp 1.65-2.5rem, lh 1.15, tracking -0.025em): `h1` tiêu đề trang.
- **Stat** (800, 2.2rem, tracking -0.04em, tabular): số thống kê; 1.7rem dưới 600px.
- **Body** (1rem, lh 1.6): nội dung; dòng phụ hero tối đa 62ch.
- **Label** (0.75rem, tracking 0.06em, hoa): `th` của bảng, nhãn thống kê.
- **Control** (0.875rem, 700 cho nút): nút, badge 0.75rem/700.

### Named Rules
**The Tabular Rule.** Mọi số cần so sánh (điểm, hạng, thời gian phạt, rating, đếm) dùng `font-variant-numeric: tabular-nums`; áp ở `table, td, th, time` và các lớp số.

## Layout

Thanh điều hướng dính trên cùng (sticky, z 1000), trang chủ rộng tối đa `--ui-page-width` 1280px; `.container` cho trang rộng tối đa 1720px, 98% chiều ngang, đệm 1.5rem. Trang quản trị dùng bố cục sidebar trái (`.layout > .side`). Nhịp khoảng cách theo rem: 0.5, 0.75, 1, 1.25, 1.5, 2rem; lề tiêu đề trang `clamp(1.25rem, 2vw, 2rem)`. Bảng dài giữ chiều rộng tối thiểu (760-1050px) và cuộn ngang. Điểm ngắt chính: 1280px (thu gọn navbar), 1100px, 720px, 600px.

## Elevation & Depth

Phẳng, phân lớp bằng tông nền và viền mảnh. Bóng chỉ là sợi hoặc nhẹ.

### Shadow Vocabulary
- **Sợi** (`--shadow-sm: 0 1px 0 rgba(11,34,54,.05)`): thẻ ở trạng thái nghỉ.
- **Nhẹ** (`--shadow-md: 0 2px 6px -1px rgba(11,34,54,.10)`): thẻ thống kê và wiki khi hover.
- **Modal** (`--shadow-lg: 0 10px 20px -6px rgba(11,34,54,.16)`): chỉ modal.
- **Vòng focus** (`--ui-ring: 0 0 0 3px rgba(10,92,143,.28)`): focus, không phải độ sâu.

### Named Rules
**The Flat Chart Rule.** Một tấm hải đồ không phát sáng. Không glow, không gradient trang trí, không nâng thẻ khi hover; hover chỉ đổi màu viền sang `primary-glow`. Token `--ui-gradient` giữ tên cho tương thích nhưng đã phẳng (một màu).

## Shapes

Góc gần vuông: 3px (badge, code, focus), 5px (nút, ô nhập), 8px (thẻ, panel, modal). Viền 1px `isobath`. Hover hàng bảng thêm vạch trái 3px `primary` (inset shadow). Chấm tròn 0.4rem đánh dấu hạng 1-3 (độ đậm 100/60/35%).

## Components

### Buttons
- **Shape:** 5px, cao tối thiểu 42px (hero 48px), chữ 700.
- **Primary:** nền `primary`, chữ `on-primary`; hover `primary-hover`; nhấn `translateY(1px) scale(.99)`.
- **Secondary:** nền `surface`, viền `isobath`, chữ `ink-secondary`; hover nền `surface-hover`, viền `primary-glow`.
- **Focus:** vòng `--ui-ring`.

### Inputs / Fields
- Nền trắng (tối: #0b1c2b), viền 1px #9fb3bd, bán kính 5px, cao 42px. Focus: viền `primary` cộng vòng 3px. Disabled: 55% độ mờ.

### Cards / Containers
- Nền `surface`, viền 1px `isobath`, 8px, bóng sợi. Hover chỉ đổi màu viền.

### Navigation
- Thanh trên: nền `--navbar-bg` 96%, viền dưới mảnh. Mục đang chọn: nền `primary-subtle`, chữ `primary`, viền trong 1px. Sidebar quản trị: mục hover/active cùng kiểu, bán kính 5px.

### Bảng và dòng bảng điểm (signature)
- Đầu bảng: nền `table-header`, nhãn 0.75rem hoa. Hàng chẵn `--table-row-even`, hover `--table-row-hover` kèm vạch trái 3px.
- Cột hạng đậm, căn giữa; điểm đậm 1.05rem màu `success`; phạt màu `ink-muted`; tất cả tabular.
- Dòng đổi hạng (`tr.rank-changed`): nền `alert-bg`, vạch trái 3px `alert`, giữ nguyên cho đến khi hover, focus hoặc click vào dòng (`scoreboard.js: markNoticed`). Dòng đổi vị trí tại chỗ bằng FLIP 420ms `cubic-bezier(.2,.8,.2,1)`, tắt khi `prefers-reduced-motion`. Mỗi dòng có `aria-label` "hạng A thành B".

### Badge
- 3px, 0.75rem, 700, hoa; nền `-bg` và viền 40% của màu trạng thái (`badge-ac`, `-wa`, `-tle`, `-pending`).

## Do's and Don'ts

### Do:
- **Do** dùng token (`var(--color-*)`) cho mọi màu để sáng và tối ngang hàng.
- **Do** để `--color-alert` dành riêng cho dòng vừa đổi hạng và giữ cho đến khi được xem.
- **Do** dùng `--color-on-primary` cho chữ trên nền `primary`.
- **Do** dùng số tabular cho mọi giá trị so sánh.
- **Do** giữ bán kính trong 3/5/8px.
- **Do** tôn trọng `prefers-reduced-motion`.

### Don't:
- **Don't** thêm gradient, glow hoặc hiệu ứng nâng khi hover.
- **Don't** dùng màu cảnh báo cam cho lỗi hay trang trí.
- **Don't** viết màu slate/tím cứng trong CSS từng trang.
- **Don't** dùng ký hiệu la bàn hay trang trí trên màn làm việc.
- **Don't** dùng bóng đổ cứng lệch hoặc bán kính ngoài 3/5/8px.

<!-- Khoảng trống đã biết, không được chuẩn hóa thành quy tắc:
- CSS từng trang (admin, auth, blog, community, components, contest-flow, courses, v.v.) còn màu slate/tím cứng (#0f172a, #1e293b, #7c3aed...) và gradient (auth, home, learning, organization, problem).
- Mũi tên chữ ▲/▼ trên dòng đổi hạng (theme.css) là ký tự glyph; chưa thay bằng SVG.
- site-refresh.css còn lưới chấm radial-gradient ở hero, gạch chân 96x4px dưới tiêu đề hero, vạch đầu thẻ thống kê và nav-links bán kính 10px: ngoài thang 3/5/8 và/hoặc trang trí; ghi nhận là nợ, không kế thừa.
- Mục điều hướng dùng bán kính 10px, bóng navbar 30px lớn hơn từ vựng bóng.
- Chưa xác lập mức WCAG mục tiêu (PRODUCT.md). -->

<!-- Review pass 1 (finish review): flattened stat cards into a compact summary row, removed hero dot grid and accent bars, added an index-contour rule (every fifth table row has a heavier line) as the chart device, added a mobile menu toggle, set link/semantic text colors to tokens, set a WCAG 2.2 AA target in PRODUCT.md. "Hải đồ" is carried by the pale chart ground, tabular numerals, index contours and the held rank-change state. -->
