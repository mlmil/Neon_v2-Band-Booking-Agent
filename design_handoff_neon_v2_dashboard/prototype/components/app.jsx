/* ============================================================
   Neon V2 — App: state, action routing, toasts, activity log, tweaks
   Core rule: protected actions NEVER apply without explicit confirmation.
   ============================================================ */

const { useState, useEffect, useCallback } = React;

const PROTECTED = {
  add_to_calendar:    { title: 'Update Google Calendar', cta: 'Add to calendar',
    body: 'Creates a new event on the public Google Calendar — this is a live write to the source of truth.',
    touches: ['Google Calendar: create event', 'Triggers downstream Band Sheet + folder sync'],
    scriptHint: 'local_venue_folder_sync.py --sync-calendar' },
  send_email:         { title: 'Send email', cta: 'Send now',
    body: 'Sends this message to the venue from the Neon V2 operational mailbox.',
    touches: ['AgentMail: deliver outbound message', 'Logs send in venue folder'],
    scriptHint: 'agentmail_send.py' },
  mark_paid_complete: { title: 'Mark payment complete', cta: 'Mark complete',
    body: 'Closes out this gig\u2019s payout and locks the entry as fully paid.',
    touches: ['Post-gig record: set PAID = TRUE', 'Locks pay/tip figures'],
    scriptHint: 'local payout ledger' },
  publish_bandsheet:  { title: 'Publish Band Sheet', cta: 'Publish',
    body: 'Publishes the private Band Sheet JSON so it becomes the trusted source for downstream checks.',
    touches: ['Band Sheet: write published JSON', 'Marks this version as the trust baseline'],
    scriptHint: 'bandsheet_verification_report.py --publish' },
  update_wordpress:   { title: 'Update WordPress', cta: 'Update post',
    body: 'Pushes this show to the public WordPress site — creates or updates the public show post.',
    touches: ['WordPress: create / update show post', 'Public-facing — visible to fans'],
    scriptHint: 'website_verification_report.py --push' },
  share_portal:       { title: 'Share venue portal files', cta: 'Share files',
    body: 'Shares the local venue folder contents to the venue\u2019s portal — files leave your Vader drive.',
    touches: ['Venue portal: upload selected files', 'External recipient gains access'],
    scriptHint: 'local_venue_folder_sync.py --share-portal' },
  change_pay_terms:   { title: 'Change pay / rate terms', cta: 'Save terms',
    body: 'Edits the agreed pay / rate terms for this gig. Affects contracts and the post-gig ledger.',
    touches: ['Gig record: overwrite pay terms', 'Post-gig ledger expectations recalculated'],
    scriptHint: 'local gig record' },
};

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "layout": "grid",
  "density": "comfortable",
  "theme": "dark",
  "hideClear": false
}/*EDITMODE-END*/;

function App() {
  const D0 = window.NEON_DATA;
  const [data, setData] = useState(() => JSON.parse(JSON.stringify(D0)));
  const [modal, setModal] = useState(null);     // {kind, ctx}
  const [confirm, setConfirm] = useState(null);  // confirm modal data
  const [toasts, setToasts] = useState([]);
  const [log, setLog] = useState([
    { t: '2026-06-09T03:55:00', kind: 'safe', msg: 'Inbox monitor wrote 2 new intake receipts.' },
    { t: '2026-06-09T03:52:00', kind: 'safe', msg: 'Calendar read-only sync OK (no writes).' },
    { t: '2026-06-09T02:31:00', kind: 'review', msg: 'New venue folder created: Tooth & Nail Winery — marked needs_review.' },
  ]);
  const [logOpen, setLogOpen] = useState(false);
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  const compact = t.density === 'compact';
  const now = data.meta.now;

  useEffect(() => { document.documentElement.setAttribute('data-theme', t.theme); }, [t.theme]);

  const toast = useCallback((msg, kind = 'safe') => {
    const id = Math.random().toString(36).slice(2);
    setToasts((p) => [...p, { id, msg, kind }]);
    setTimeout(() => setToasts((p) => p.filter((x) => x.id !== id)), 3600);
  }, []);
  const addLog = useCallback((msg, kind = 'safe') => {
    setLog((p) => [{ t: new Date().toISOString(), kind, msg }, ...p]);
  }, []);

  const mutate = (fn) => setData((d) => { const n = JSON.parse(JSON.stringify(d)); fn(n); return n; });

  // ---- low-level apply (after confirmation for protected) ----
  function apply(type, p) {
    switch (type) {
      case 'create_receipt':
        toast('Local intake receipt created'); addLog('Created intake receipt for ' + p.venue + ' (' + p.id + ').'); break;
      case 'mark_reviewed':
        mutate((d) => { const r = d.intake_receipts.find((x) => x.id === p.id); if (r) r.status = 'reviewed'; });
        toast('Marked reviewed'); addLog('Intake ' + p.id + ' (' + p.venue + ') marked reviewed.'); setModal(null); break;
      case 'save_draft':
        toast('Draft saved locally (Gmail fallback)'); addLog('Saved email draft to ' + (p.to || 'venue') + ' — not sent.', 'draft'); setModal(null); break;
      case 'save_payout':
        mutate((d) => { const it = d.post_gig_items.find((x) => x.id === p.id); if (it) {
          it.base_pay = num(p.base_pay); it.tips = num(p.tips); it.still_owed = num(p.still_owed);
          it.method = p.method; it.received_by = p.received_by; it.notes = p.notes;
          it.status = num(p.still_owed) > 0 ? 'needs_review' : 'success';
        }});
        toast('Payout entry saved locally'); addLog('Saved payout for ' + p.venue + ' — base $' + (p.base_pay||0) + ', tips $' + (p.tips||0) + '.'); setModal(null); break;
      case 'add_note':
        toast('Note added'); addLog('Note on ' + (p.label || 'item') + ': "' + (p.note || '').slice(0, 60) + '"', 'review'); setModal(null); break;
      case 'run_checks':
        toast('Ran checks for ' + p.venue); addLog('Ran Band Sheet + website checks for ' + p.venue + '.'); break;
      case 'run_all_checks': case 'run_all':
        mutate((d) => d.checks.forEach((c) => c.last_run = nowISO()));
        toast('All accuracy checks re-run'); addLog('Re-ran all accuracy checks.'); break;
      case 'run_bandsheet':
        mutate((d) => { const c = d.checks.find((x) => x.kind === 'bandsheet'); if (c) c.last_run = nowISO(); });
        toast('Band Sheet check complete — 1 mismatch'); addLog('Ran bandsheet_verification_report.py — mismatch persists.'); break;
      case 'run_website':
        mutate((d) => { const c = d.checks.find((x) => x.kind === 'website'); if (c) c.last_run = nowISO(); });
        toast('Website check complete'); addLog('Ran website_verification_report.py.'); break;
      case 'run_agentmail_health':
        toast('AgentMail health check: still DOWN (401)', 'bad'); addLog('Ran agentmail_health_check.py — auth error, send stays disabled.', 'bad'); break;
      case 'open_folder':
        toast('Opening ' + (p.venue || 'folder') + ' in Finder'); addLog('Opened local folder: ' + (p.path || p.venue) + '.'); break;
      case 'create_folder':
        mutate((d) => { d.venue_folders.unshift({ id: 'VF-NEW' + Date.now().toString().slice(-4), status: 'needs_review',
          venue: 'New Venue (rename)', date: now.slice(0,10), path: '/Venues/New Venue/New Venue - ' + now.slice(0,10) + '/',
          receipt: true, digest: false, reviewed: false, note: 'NEW folder created. Digest skipped (local model offline). Verify venue name/contact/date.' }); });
        toast('New folder created — needs_review', 'review'); addLog('Created new local venue folder — marked needs_review.', 'review'); break;
      case 'mark_folder_reviewed':
        mutate((d) => { const v = d.venue_folders.find((x) => x.id === p.id); if (v) { v.reviewed = true; v.status = 'success'; } });
        toast('Venue receipt reviewed'); addLog('Marked venue folder reviewed: ' + p.venue + '.'); break;
      case 'rerun_digest':
        toast('Local model offline — digest queued', 'review'); addLog('Digest requested for ' + (p.venue || 'pending') + ' — queued (model offline).', 'review'); break;
      case 'retry_local_model':
        toast('Retry failed — model still offline', 'bad'); addLog('Retried local model connection — still offline.', 'bad'); break;
      case 'rerun_sync':
        mutate((d) => d.meta.last_full_sync = nowISO()); toast('Calendar re-checked (read-only)'); addLog('Re-ran read-only calendar sync.'); break;
      case 'mark_lead_reviewed':
        mutate((d) => { const s = d.scout_leads.find((x) => x.id === p.id); if (s) s.status = 'reviewed'; });
        toast('Lead marked reviewed'); addLog('Scout lead reviewed: ' + p.venue + '.'); break;
      // ---- post-confirmation protected ----
      case '_confirm_booking':
        mutate((d) => { const g = d.gigs.find((x) => x.id === p.id); if (g && g.status !== 'blocked') { g.confirmed = true; g.status = 'success'; } });
        toast('Booking marked fully confirmed'); addLog('APPROVED: marked ' + p.venue + ' booking fully confirmed.', 'protected'); break;
      case 'add_to_calendar':
        mutate((d) => { const r = d.intake_receipts.find((x) => x.id === p.id); if (r) r.status = 'reviewed'; });
        toast('Event added to Google Calendar'); addLog('APPROVED: added ' + p.venue + ' to Google Calendar.', 'protected'); setModal(null); break;
      case 'send_email':
        toast('Email sent via AgentMail'); addLog('APPROVED: sent email to ' + (p.to || 'venue') + '.', 'protected'); setModal(null); break;
      case 'mark_paid_complete':
        mutate((d) => { const it = d.post_gig_items.find((x) => x.id === p.id); if (it) { it.paid_complete = true; it.status = 'success'; it.still_owed = 0; } });
        toast('Payment marked complete'); addLog('APPROVED: marked ' + p.venue + ' payment complete.', 'protected'); setModal(null); break;
      case 'publish_bandsheet':
        mutate((d) => { const g = d.gigs.find((x) => x.id === p.id); if (g) g.bandsheet_match = true;
          const c = d.checks.find((x) => x.kind === 'bandsheet'); if (c) { c.status = 'success'; c.last_run = nowISO(); c.result = 'No mismatches — Band Sheet published as trust baseline.'; } });
        toast('Band Sheet published'); addLog('APPROVED: published Band Sheet (baseline for ' + p.venue + ').', 'protected'); break;
      case 'update_wordpress':
        mutate((d) => { const g = d.gigs.find((x) => x.id === p.id); if (g) g.website_match = true;
          const c = d.checks.find((x) => x.kind === 'website'); if (c) { c.status = 'success'; c.last_run = nowISO(); c.result = 'All shows have matching WordPress posts.'; } });
        toast('WordPress show post updated'); addLog('APPROVED: updated WordPress post for ' + p.venue + '.', 'protected'); break;
      case 'share_portal':
        toast('Venue portal files shared'); addLog('APPROVED: shared venue portal files for ' + p.venue + '.', 'protected'); break;
      case 'change_pay_terms':
        mutate((d) => { const g = d.gigs.find((x) => x.id === p.id); if (g) g.pay_terms = p.pay_terms; });
        toast('Pay / rate terms updated'); addLog('APPROVED: changed pay terms for ' + p.venue + '.', 'protected'); break;
      default: break;
    }
  }

  // ---- public dispatch ----
  const H = {
    act(type, p) {
      if (type === 'draft_email') { setModal({ kind: 'draft', ctx: { title: 'Reply · ' + p.venue, to: p.sender, subject: 'Re: Neon Blonde — ' + p.venue, body: p.ack_draft } }); return; }
      if (PROTECTED[type]) {
        const base = PROTECTED[type];
        let blockedReason = null;
        if (type === 'send_email') { const am = data.agent_status.find((a) => a.key === 'agentmail'); if (am.status === 'blocked') blockedReason = 'AgentMail is down (401). Direct send is disabled — use “Save draft” for the Gmail fallback instead.'; }
        if (type === 'mark_paid_complete' && num(p.still_owed) > 0) blockedReason = '$' + num(p.still_owed) + ' is still owed. Clear the balance to $0 before marking complete.';
        if (type === 'share_portal') { const vf = data.venue_folders.find((v) => v.id === p.folder_id); if (vf && !vf.reviewed) blockedReason = 'Venue folder is still unreviewed. Mark the receipt reviewed before sharing files externally.'; }
        if (type === 'update_wordpress' && p.status === 'blocked') blockedReason = 'This gig has an open Band Sheet mismatch. Resolve it before pushing public WordPress changes.';
        setConfirm({ ...base, blockedReason, onConfirm: () => { apply(type, p); setConfirm(null); } });
        return;
      }
      apply(type, p);
    },
    confirmAction(d) { setConfirm({ ...d, onConfirm: () => { d.onConfirm(); setConfirm(null); } }); },
    openIntake(rec) { setModal({ kind: 'intake', ctx: rec }); },
    openMoney(item) { setModal({ kind: 'money', ctx: item }); },
    openDraft(ctx) { setModal({ kind: 'draft', ctx }); },
    openNote(ctx) { setModal({ kind: 'note', ctx }); },
    openGig(gig) { setModal({ kind: 'gig', ctx: gig }); },
    scrollTo(id) { const el = document.querySelector('[data-anchor="' + id + '"]'); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 90, behavior: 'smooth' }); },
  };

  const agentmailDown = data.agent_status.find((a) => a.key === 'agentmail').status === 'blocked';
  const hc = t.hideClear;
  const cp = compact;

  // panel elements keyed for layout reuse
  const panels = {
    intake:     <div data-anchor="panel-intake"><IntakeQueue data={data} H={H} hideClear={hc} compact={cp} /></div>,
    booking:    <div data-anchor="panel-booking"><BookingQueue data={data} H={H} hideClear={hc} compact={cp} /></div>,
    checks:     <div data-anchor="panel-checks"><AccuracyChecks data={data} H={H} compact={cp} /></div>,
    folders:    <div data-anchor="panel-folders"><VenueFolders data={data} H={H} hideClear={hc} compact={cp} /></div>,
    money:      <div data-anchor="panel-money"><MoneyQueue data={data} H={H} hideClear={hc} compact={cp} /></div>,
    agentmail:  <div data-anchor="panel-agentmail"><AgentMailStatus data={data} H={H} compact={cp} /></div>,
    localmodel: <div data-anchor="panel-localmodel"><LocalModelStatus data={data} H={H} compact={cp} /></div>,
    scout:      <div data-anchor="panel-scout"><ScoutLeads data={data} H={H} hideClear={hc} compact={cp} /></div>,
  };

  return (
    <div style={{ minHeight: '100vh', paddingBottom: 60 }}>
      <TopNav data={data} log={log} onLog={() => setLogOpen(true)} />
      <div style={{ padding: '0 var(--page-pad-x)' }}>
        <div style={{ maxWidth: 1560, margin: '0 auto' }}>
          <div style={{ padding: '22px 0 0' }}><TodayStrip data={data} H={H} /></div>

          {/* layout: grid (masonry) or swimlanes */}
          {t.layout === 'grid' ? (
            <div className="nb-grid" style={{ marginTop: 20 }}>
              {Object.entries(panels).map(([k, el]) => <React.Fragment key={k}>{el}</React.Fragment>)}
            </div>
          ) : (
            <Swimlanes panels={panels} />
          )}
        </div>
      </div>

      {/* TWEAKS */}
      <TweaksPanel>
        <TweakSection label="Layout" />
        <TweakRadio label="Arrangement" value={t.layout} options={['grid', 'swimlanes']} onChange={(v) => setTweak('layout', v)} />
        <TweakRadio label="Density" value={t.density} options={['compact', 'comfortable']} onChange={(v) => setTweak('density', v)} />
        <TweakToggle label="Hide all-clear items" value={t.hideClear} onChange={(v) => setTweak('hideClear', v)} />
        <TweakSection label="Theme" />
        <TweakRadio label="Mode" value={t.theme} options={['dark', 'light']} onChange={(v) => setTweak('theme', v)} />
      </TweaksPanel>

      {/* MODALS */}
      {modal && modal.kind === 'intake' && <IntakeModal rec={modal.ctx} onClose={() => setModal(null)} act={H.act} />}
      {modal && modal.kind === 'money' && <MoneyModal item={modal.ctx} onClose={() => setModal(null)} act={H.act} />}
      {modal && modal.kind === 'draft' && <DraftModal ctx={modal.ctx} onClose={() => setModal(null)} act={H.act} agentmailDown={agentmailDown} />}
      {modal && modal.kind === 'note' && <NoteModal ctx={modal.ctx} onClose={() => setModal(null)} act={H.act} />}
      {modal && modal.kind === 'gig' && <GigDetailModal gig={modal.ctx} data={data} onClose={() => setModal(null)} H={H} />}
      {confirm && <ConfirmModal data={confirm} onClose={() => setConfirm(null)} onConfirm={confirm.onConfirm} />}

      {/* ACTIVITY LOG drawer */}
      {logOpen && <LogDrawer log={log} onClose={() => setLogOpen(false)} now={now} />}

      {/* TOASTS */}
      <div style={{ position: 'fixed', left: 20, bottom: 20, zIndex: 150, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {toasts.map((x) => (
          <div key={x.id} className="nb-toast" style={{ background: 'var(--surface)', border: '1px solid var(--rule)',
            borderLeft: '3px solid ' + (x.kind === 'bad' ? 'var(--bad)' : x.kind === 'review' ? 'var(--warn)' : x.kind === 'protected' ? 'var(--bad)' : 'var(--ok)'),
            padding: '11px 15px', display: 'flex', alignItems: 'center', gap: 9, minWidth: 240, maxWidth: 360 }}>
            <span style={{ color: x.kind === 'bad' ? 'var(--bad)' : x.kind === 'review' ? 'var(--warn)' : 'var(--ok)', display: 'flex' }}>
              <Icon name={x.kind === 'bad' ? 'alert' : 'check'} size={15} />
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)' }}>{x.msg}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---- top nav ---- */
function TopNav({ data, log, onLog }) {
  return (
    <div style={{ position: 'sticky', top: 0, zIndex: 100, background: 'var(--bg)', borderBottom: '1px solid var(--rule)' }}>
      <div style={{ padding: '0 var(--page-pad-x)' }}>
        <div style={{ maxWidth: 1560, margin: '0 auto', height: 'var(--nav-h)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
            <img src="assets/spark-plug-bone.png" alt="" style={{ height: 30, width: 'auto', display: 'block', opacity: 0.92 }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, letterSpacing: '-0.01em', color: 'var(--fg)' }}>
                NEON<span style={{ color: 'var(--accent)' }}>.</span>V2
              </div>
              <div style={{ width: 1, height: 14, background: 'var(--rule)', flexShrink: 0 }} className="nb-hide-md" />
              <Label size={10} ls="0.1em" className="nb-hide-md" style={{ whiteSpace: 'nowrap' }}>Operations Dashboard</Label>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <a href={data.meta.calendar_url} target="_blank" rel="noopener noreferrer" title="Open the Fresh Ground Sound rehearsal space calendar"
              className="nb-btn nb-btn--default" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: 'pointer', textDecoration: 'none',
              fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500,
              padding: '7px 11px', color: 'var(--fg-muted-2)', border: '1px solid var(--rule)', background: 'transparent', minHeight: 32, whiteSpace: 'nowrap' }}>
              <Icon name="calendar" size={13} /> Fresh Ground Sound <Icon name="open" size={11} />
            </a>
            <a href={data.meta.bandsheet_url} target="_blank" rel="noopener noreferrer" title="Open the private Band Sheet"
              className="nb-btn nb-btn--default" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: 'pointer', textDecoration: 'none',
              fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500,
              padding: '7px 11px', color: 'var(--fg-muted-2)', border: '1px solid var(--rule)', background: 'transparent', minHeight: 32, whiteSpace: 'nowrap' }}>
              <Icon name="sheet" size={13} /> Band Sheet <Icon name="open" size={11} />
            </a>
            <div style={{ width: 1, height: 18, background: 'var(--rule)' }} className="nb-hide-sm" />
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, border: '1px solid var(--accent)', padding: '5px 10px', whiteSpace: 'nowrap' }} className="nb-hide-sm">
              <Icon name="lock" size={12} color="var(--accent)" sw={2} />
              <Label size={10} color="var(--accent)" ls="0.08em" style={{ fontWeight: 500 }}>Internal · Supervised</Label>
            </span>
            <button onClick={onLog} className="nb-btn nb-btn--default" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: 'pointer',
              fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500,
              padding: '7px 11px', color: 'var(--fg-muted-2)', border: '1px solid var(--rule)', background: 'transparent', minHeight: 32, whiteSpace: 'nowrap' }}>
              <Icon name="note" size={13} /> Activity ({log.length})
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---- swimlanes layout ---- */
function Swimlanes({ panels }) {
  const col = { display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 };
  return (
    <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="nb-swim">
        <div style={col}><LaneLabel n="01" t="Intake" />{panels.intake}{panels.scout}</div>
        <div style={col}><LaneLabel n="02" t="Booking & Verification" />{panels.booking}{panels.checks}{panels.folders}</div>
        <div style={col}><LaneLabel n="03" t="Post-Gig & Systems" />{panels.money}{panels.agentmail}{panels.localmodel}</div>
      </div>
    </div>
  );
}
function LaneLabel({ n, t }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 4 }}>
      <Label size={11} color="var(--accent)" ls="0.1em">§ {n}</Label>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 600, letterSpacing: '-0.01em', color: 'var(--fg)' }}>{t}</span>
      <div style={{ flex: 1, height: 1, background: 'var(--rule)' }} />
    </div>
  );
}

/* ---- activity log drawer ---- */
function LogDrawer({ log, onClose, now }) {
  const kc = { safe: 'var(--ok)', review: 'var(--warn)', draft: 'var(--fg-muted)', protected: 'var(--bad)', bad: 'var(--bad)' };
  return (
    <div onMouseDown={onClose} style={{ position: 'fixed', inset: 0, zIndex: 180, background: 'rgba(8,9,10,0.5)', display: 'flex', justifyContent: 'flex-end' }}>
      <div onMouseDown={(e) => e.stopPropagation()} style={{ width: 420, maxWidth: '92vw', height: '100%', background: 'var(--surface)', borderLeft: '1px solid var(--rule)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--rule)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Label size={10} color="var(--accent)" style={{ display: 'block', marginBottom: 4 }}>Local activity log</Label>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600, color: 'var(--fg)' }}>Receipts & approvals</div>
          </div>
          <button onClick={onClose} className="nb-x" style={{ background: 'transparent', border: '1px solid var(--rule)', color: 'var(--fg-muted)', cursor: 'pointer', padding: 6, display: 'flex', lineHeight: 0 }}><Icon name="x" size={16} /></button>
        </div>
        <div style={{ overflowY: 'auto', padding: '14px 22px', display: 'flex', flexDirection: 'column', gap: 0 }}>
          {log.map((e, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: '1px solid var(--rule-soft)' }}>
              <span style={{ width: 7, height: 7, background: kc[e.kind] || 'var(--fg-muted)', flexShrink: 0, marginTop: 5 }} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)', lineHeight: 1.45 }}>{e.msg}</div>
                <Label size={9.5} style={{ display: 'block', marginTop: 3 }}>{e.kind === 'protected' ? 'APPROVED · ' : ''}{relTime(e.t, now)} · {fmtClock(e.t)}</Label>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function num(v) { const n = Number(v); return isNaN(n) ? 0 : n; }
function nowISO() { return new Date().toISOString(); }

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
