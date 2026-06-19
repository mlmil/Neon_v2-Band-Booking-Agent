/* ============================================================
   Neon V2 — shared UI primitives (Civic Grid)
   Exported to window for use across Babel scripts.
   ============================================================ */
const { useState, useEffect, useRef, useCallback } = React;

/* ---- status taxonomy ---- */
const STATUS = {
  success:      { label: 'OK',           cssVar: 'var(--ok)',   key: 'success' },
  needs_review: { label: 'NEEDS REVIEW', cssVar: 'var(--warn)', key: 'needs_review' },
  blocked:      { label: 'BLOCKED',      cssVar: 'var(--bad)',  key: 'blocked' },
  pending:      { label: 'PENDING',      cssVar: 'var(--idle)', key: 'pending' },
  reviewed:     { label: 'REVIEWED',     cssVar: 'var(--ok)',   key: 'reviewed' },
};
const statusColor = (s) => (STATUS[s] || STATUS.pending).cssVar;
const statusLabel = (s) => (STATUS[s] || STATUS.pending).label;
const statusRank  = { blocked: 0, needs_review: 1, pending: 2, success: 3, reviewed: 4 };

/* ---- mono label ---- */
function Label({ children, color, ls = '0.08em', size = 11, style, className }) {
  return (
    <span className={className} style={{ fontFamily: 'var(--font-mono)', fontSize: size, letterSpacing: ls, lineHeight: 1.35,
      textTransform: 'uppercase', color: color || 'var(--fg-muted)', fontWeight: 400, ...style }}>
      {children}
    </span>
  );
}

/* ---- status chip: square dot + mono label ---- */
function StatusChip({ status, size = 10 }) {
  const c = statusColor(status);
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
      <span style={{ width: size, height: size, background: c, flexShrink: 0 }} />
      <Label color={c} ls="0.1em" style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>{statusLabel(status)}</Label>
    </span>
  );
}

/* ---- icon library (24x24, stroke 1.6, round) ---- */
function Icon({ name, size = 18, color = 'currentColor', sw = 1.6 }) {
  const p = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: color,
    strokeWidth: sw, strokeLinecap: 'round', strokeLinejoin: 'round' };
  switch (name) {
    case 'inbox':    return (<svg {...p}><path d="M3 13l2.5-8h13L21 13"/><path d="M3 13v6h18v-6"/><path d="M3 13h5l1.5 2.5h5L16 13h5"/></svg>);
    case 'calendar': return (<svg {...p}><rect x="3" y="4.5" width="18" height="16" rx="0"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/></svg>);
    case 'folder':   return (<svg {...p}><path d="M3 6h6l2 2.5h10V19H3z"/></svg>);
    case 'check-doc':return (<svg {...p}><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 14l2 2 3.5-3.5"/></svg>);
    case 'mail':     return (<svg {...p}><rect x="3" y="5" width="18" height="14" rx="0"/><path d="M3 6l9 7 9-7"/></svg>);
    case 'money':    return (<svg {...p}><rect x="2.5" y="6" width="19" height="12" rx="0"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v5M18 9.5v5"/></svg>);
    case 'cpu':      return (<svg {...p}><rect x="6" y="6" width="12" height="12" rx="0"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2.5v3.5M15 2.5v3.5M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/></svg>);
    case 'scout':    return (<svg {...p}><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/><path d="M11 8v6M8 11h6"/></svg>);
    case 'refresh':  return (<svg {...p}><path d="M20 11a8 8 0 10-2.3 6"/><path d="M20 5v6h-6"/></svg>);
    case 'check':    return (<svg {...p}><path d="M5 12.5l4.5 4.5L19 7"/></svg>);
    case 'alert':    return (<svg {...p}><path d="M10.3 3.9L2.5 17a2 2 0 001.7 3h15.6a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/><path d="M12 9v4.5"/><circle cx="12" cy="16.6" r="0.9" fill={color} stroke="none"/></svg>);
    case 'clock':    return (<svg {...p}><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>);
    case 'lock':     return (<svg {...p} strokeWidth="2" strokeLinecap="square"><rect x="4" y="10.5" width="16" height="10" rx="0"/><path d="M8 10.5V7a4 4 0 018 0v3.5"/></svg>);
    case 'plus':     return (<svg {...p}><path d="M12 5v14M5 12h14"/></svg>);
    case 'note':     return (<svg {...p}><path d="M5 4h14v11l-5 5H5z"/><path d="M14 20v-5h5"/></svg>);
    case 'eye':      return (<svg {...p}><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.6"/></svg>);
    case 'send':     return (<svg {...p}><path d="M21 3L10.5 13.5M21 3l-7 18-3.5-7.5L3 10z"/></svg>);
    case 'x':        return (<svg {...p}><path d="M6 6l12 12M18 6L6 18"/></svg>);
    case 'arrow':    return (<svg {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>);
    case 'open':     return (<svg {...p}><path d="M14 4h6v6M20 4l-9 9"/><path d="M19 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1h5"/></svg>);
    case 'pin':      return (<svg {...p}><path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.4"/></svg>);
    case 'flag':     return (<svg {...p}><path d="M5 21V4M5 4h12l-2.5 4L17 12H5"/></svg>);
    case 'globe':    return (<svg {...p}><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.6 2.5 14.4 0 17M12 3.5c-2.5 2.6-2.5 14.4 0 17"/></svg>);
    case 'sheet':    return (<svg {...p}><rect x="4" y="3" width="16" height="18"/><path d="M4 9h16M4 15h16M10 3v18"/></svg>);
    default:         return null;
  }
}

/* ---- buttons ---- */
function Btn({ icon, children, onClick, disabled, variant = 'default', title }) {
  // variant: default (outline), amber, ghost
  const base = {
    display: 'inline-flex', alignItems: 'center', gap: 7, cursor: disabled ? 'not-allowed' : 'pointer',
    fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.06em', textTransform: 'uppercase',
    fontWeight: 500, padding: '7px 11px', borderRadius: 0, lineHeight: 1, whiteSpace: 'nowrap',
    transition: 'background var(--dur) var(--ease), color var(--dur) var(--ease), border-color var(--dur)',
    background: 'transparent', minHeight: 32,
  };
  const skins = {
    default: { color: disabled ? 'var(--fg-muted)' : 'var(--fg-muted-2)', border: '1px solid var(--rule)' },
    amber:   { color: 'var(--accent)', border: '1px solid var(--accent)' },
    ghost:   { color: 'var(--fg-muted)', border: '1px solid transparent' },
  };
  const cls = 'nb-btn nb-btn--' + variant;
  return (
    <button className={cls} title={title} onClick={disabled ? undefined : onClick} disabled={disabled}
      style={{ ...base, ...skins[variant], opacity: disabled ? 0.45 : 1 }}>
      {icon && <Icon name={icon} size={13} />}
      {children}
    </button>
  );
}

/* protected action button: amber w/ lock, signals confirmation required */
function ProtectedBtn({ icon = 'lock', children, onClick, title }) {
  return (
    <button className="nb-btn nb-btn--protected" title={title || 'Requires confirmation'} onClick={onClick}
      style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: 'pointer',
        fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.06em', textTransform: 'uppercase',
        fontWeight: 600, padding: '7px 11px', borderRadius: 0, lineHeight: 1, whiteSpace: 'nowrap', minHeight: 32,
        color: 'var(--bad)', border: '1px solid var(--bad)', background: 'transparent',
        transition: 'background var(--dur) var(--ease), color var(--dur) var(--ease)' }}>
      <Icon name={icon} size={12} sw={2} />
      {children}
    </button>
  );
}

/* ---- panel shell ---- */
function Panel({ id, title, icon, section, status, count, children, blocked, compact, headerRight }) {
  const isBlocked = blocked || status === 'blocked';
  const isWarn = status === 'needs_review';
  const pad = compact ? 16 : 20;
  return (
    <section data-screen-label={title} data-panel={id}
      style={{
        background: 'var(--surface)',
        border: '1px solid ' + (isBlocked ? 'var(--bad)' : isWarn ? 'var(--rule)' : 'var(--rule)'),
        borderTop: isBlocked ? '3px solid var(--bad)' : isWarn ? '3px solid var(--warn)' : '3px solid var(--rule)',
        display: 'flex', flexDirection: 'column', minWidth: 0,
      }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', rowGap: 8,
        padding: pad + 'px ' + pad + 'px ' + (compact ? 12 : 14) + 'px',
        borderBottom: '1px solid var(--rule)',
        background: isBlocked ? 'color-mix(in srgb, var(--bad) 9%, transparent)'
          : isWarn ? 'color-mix(in srgb, var(--warn) 7%, transparent)' : 'transparent' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span style={{ color: isBlocked ? 'var(--bad)' : 'var(--accent)', display: 'flex', flexShrink: 0 }}>
            <Icon name={icon} size={17} />
          </span>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, minWidth: 0, flexWrap: 'wrap' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: compact ? 14.5 : 15.5,
                fontWeight: 600, letterSpacing: '-0.01em', color: 'var(--fg)', minWidth: 0, lineHeight: 1.2, whiteSpace: 'nowrap' }}>{title}</span>
              {typeof count === 'number' && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)', flexShrink: 0 }}>{count}</span>
              )}
            </div>
            {section && <Label size={9.5} ls="0.1em" style={{ display: 'block', marginTop: 3, whiteSpace: 'nowrap' }}>{section}</Label>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          {headerRight}
          {status && <StatusChip status={status} />}
        </div>
      </div>
      {/* body */}
      <div style={{ padding: pad + 'px', display: 'flex', flexDirection: 'column', gap: compact ? 10 : 12, flex: 1 }}>
        {children}
      </div>
    </section>
  );
}

/* small key/value meta row */
function Meta({ k, v, vColor, nowrap }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, minWidth: 0 }}>
      <Label size={10} ls="0.07em" style={{ flexShrink: 0, width: 74, color: 'var(--fg-muted)' }}>{k}</Label>
      <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: vColor || 'var(--fg)', minWidth: 0, lineHeight: 1.4, whiteSpace: nowrap ? 'nowrap' : 'normal' }}>{v}</span>
    </div>
  );
}

/* row item inside a panel (one gig / receipt / lead) */
function Item({ children, status, onClick, flush }) {
  const isBlocked = status === 'blocked';
  const isWarn = status === 'needs_review';
  return (
    <div onClick={onClick} className="nb-item"
      style={{ border: '1px solid var(--rule)', padding: flush ? 0 : '12px 13px',
        borderLeft: '3px solid ' + (isBlocked ? 'var(--bad)' : isWarn ? 'var(--warn)' : 'var(--rule)'),
        cursor: onClick ? 'pointer' : 'default',
        background: isBlocked ? 'color-mix(in srgb, var(--bad) 6%, transparent)' : 'transparent',
        display: 'flex', flexDirection: 'column', gap: 8 }}>
      {children}
    </div>
  );
}

function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso + (iso.length === 10 ? 'T00:00:00' : ''));
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}
function fmtTime(hhmm) {
  if (!hhmm) return '—';
  const [h, m] = hhmm.split(':').map(Number);
  const ap = h >= 12 ? 'PM' : 'AM';
  const h12 = ((h + 11) % 12) + 1;
  return h12 + (m ? ':' + String(m).padStart(2, '0') : '') + ' ' + ap;
}
function fmtClock(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}
function relTime(iso, now) {
  if (!iso) return '—';
  const ms = new Date(now).getTime() - new Date(iso).getTime();
  const m = Math.round(ms / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return m + 'm ago';
  const h = Math.round(m / 60);
  if (h < 24) return h + 'h ago';
  return Math.round(h / 24) + 'd ago';
}
function daysUntil(dateStr, now) {
  const d = new Date(dateStr + 'T00:00:00').getTime();
  const n = new Date(now.slice(0, 10) + 'T00:00:00').getTime();
  return Math.round((d - n) / 86400000);
}

Object.assign(window, {
  Label, StatusChip, Icon, Btn, ProtectedBtn, Panel, Meta, Item,
  STATUS, statusColor, statusLabel, statusRank,
  fmtDate, fmtTime, fmtClock, relTime, daysUntil,
});
