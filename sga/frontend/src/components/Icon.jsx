const icons = {
  grid: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="2" width="7" height="7" rx="1" />
      <rect x="11" y="2" width="7" height="7" rx="1" />
      <rect x="2" y="11" width="7" height="7" rx="1" />
      <rect x="11" y="11" width="7" height="7" rx="1" />
    </svg>
  ),
  building: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 18V6l7-4 7 4v12" />
      <path d="M8 18v-5h4v5" />
      <path d="M3 18h14" />
      <rect x="7" y="7" width="2" height="2" />
      <rect x="11" y="7" width="2" height="2" />
    </svg>
  ),
  library: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 3h2v14H4zM9 3h2v14H9zM14 3l2 14" />
    </svg>
  ),
  calendar: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="4" width="16" height="14" rx="2" />
      <path d="M2 8h16" />
      <path d="M6 2v4M14 2v4" />
      <rect x="5" y="11" width="2" height="2" rx=".5" fill="currentColor" stroke="none" />
      <rect x="9" y="11" width="2" height="2" rx=".5" fill="currentColor" stroke="none" />
      <rect x="13" y="11" width="2" height="2" rx=".5" fill="currentColor" stroke="none" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="7" cy="7" r="3" />
      <path d="M1 18c0-3.314 2.686-6 6-6s6 2.686 6 6" />
      <path d="M14 6a3 3 0 0 1 0 6M19 18c0-2.761-2.239-5-5-5" />
    </svg>
  ),
  user: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="7" r="4" />
      <path d="M2 18c0-4.418 3.582-8 8-8s8 3.582 8 8" />
    </svg>
  ),
  lock: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="4" y="9" width="12" height="9" rx="2" />
      <path d="M7 9V6a3 3 0 0 1 6 0v3" />
      <circle cx="10" cy="14" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  ),
  clipboard: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="4" y="4" width="12" height="14" rx="2" />
      <path d="M8 4V3a2 2 0 0 1 4 0v1" />
      <path d="M7 9h6M7 12h4" />
    </svg>
  ),
  'graduation-cap': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 3L1 8l9 5 9-5-9-5z" />
      <path d="M5 10.5v4c0 1.657 2.239 3 5 3s5-1.343 5-3v-4" />
      <path d="M19 8v5" />
    </svg>
  ),
  document: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M6 2h8l4 4v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
      <path d="M14 2v4h4" />
      <path d="M7 9h6M7 12h4" />
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M13 3h4a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-4" />
      <path d="M9 14l5-4-5-4" />
      <path d="M14 10H3" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="8.5" cy="8.5" r="5.5" />
      <path d="M13 13l4 4" />
    </svg>
  ),
  warning: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 2L1 17h18L10 2z" />
      <path d="M10 8v4M10 14.5v.5" strokeLinecap="round" />
    </svg>
  ),
  'check-circle': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M6.5 10.5l2.5 2.5 5-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  download: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 3v10M6 9l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 15v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1" />
    </svg>
  ),
  edit: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M14.5 2.5l3 3L6 17H3v-3L14.5 2.5z" />
    </svg>
  ),
  ban: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M4.5 4.5l11 11" />
    </svg>
  ),
  play: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M8 7l6 3-6 3V7z" fill="currentColor" stroke="none" />
    </svg>
  ),
  pause: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M8 7v6M12 7v6" strokeLinecap="round" />
    </svg>
  ),
  globe: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M10 2c-2 3-3 5-3 8s1 5 3 8M10 2c2 3 3 5 3 8s-1 5-3 8M2 10h16" />
    </svg>
  ),
  'bar-chart': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 17V9M8 17V5M13 17v-6M18 17V7" strokeLinecap="round" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="2.5" />
      <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4" strokeLinecap="round" />
    </svg>
  ),
  inbox: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="4" width="16" height="13" rx="2" />
      <path d="M2 11h4l2 3h4l2-3h4" />
    </svg>
  ),
  'chevron-right': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M7 4l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'chevron-left': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M13 4l-6 6 6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  check: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 10l4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  save: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 2h10l4 4v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
      <rect x="7" y="2" width="6" height="5" rx="0.5" />
      <rect x="5" y="12" width="10" height="6" rx="1" />
    </svg>
  ),
  megaphone: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 9v2a1 1 0 0 0 1 1h2l4 4V5L6 9H4a1 1 0 0 0-1 1z" />
      <path d="M15 7a4 4 0 0 1 0 6" strokeLinecap="round" />
    </svg>
  ),
  pin: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 2l2 6h4l-3 4-1 5-2-3-2 3-1-5-3-4h4l2-6z" />
    </svg>
  ),
  info: (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M10 9v5M10 6.5v.5" strokeLinecap="round" />
    </svg>
  ),
  'arrow-right': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 10h12M12 6l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'clock': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8" />
      <path d="M10 6v4l3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'x': (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M5 5l10 10M15 5L5 15" strokeLinecap="round" />
    </svg>
  ),
}

export default function Icon({ name, size = 16, className = '', style = {} }) {
  const svg = icons[name]
  if (!svg) return null
  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: size,
        height: size,
        flexShrink: 0,
        ...style,
      }}
    >
      {svg}
    </span>
  )
}
