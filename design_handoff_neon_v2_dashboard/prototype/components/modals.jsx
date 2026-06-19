/* ============================================================
   Neon V2 — modals & overlays
   ConfirmModal gates every PROTECTED action behind an explicit step.
   ============================================================ */

const { useState, useEffect } = React;

function Overlay({ onClose, children, width = 560 }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div onMouseDown={onClose} style={{ position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(8,9,10,0.66)', display: 'flex', alignItems: 'flex-start',
      justifyContent: 'center', padding: '64px 20px', overflowY: 'auto' }}>
      <div onMouseDown={(e) => e.stopPropagation()} style={{ width: '100%', maxWidth: width,
        background: 'var(--surface)', border: '1px solid var(--rule)', borderTop: '3px solid var(--accent)' }}>
        {children}
      </div>
    </div>
  );
}

function ModalHead({ icon, label, title, onClose, danger }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
      padding: '18px 22px', borderBottom: '1px solid var(--rule)' }}>
      <div style={{ display: 'flex', gap: 11, minWidth: 0 }}>
        <span style={{ color: danger ? 'var(--bad)' : 'var(--accent)', display: 'flex', marginTop: 2, flexShrink: 0 }}>
          <Icon name={icon} size={20} />
        </span>
        <div style={{ minWidth: 0 }}>
          {label && <Label size={10} color={danger ? 'var(--bad)' : 'var(--accent)'} style={{ display: 'block', marginBottom: 6 }}>{label}</Label>}
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--fg)', lineHeight: 1.15 }}>{title}</div>
        </div>
      </div>
      <button onClick={onClose} className="nb-x" style={{ background: 'transparent', border: '1px solid var(--rule)',
        color: 'var(--fg-muted)', cursor: 'pointer', padding: 6, display: 'flex', lineHeight: 0 }}>
        <Icon name="x" size={16} />
      </button>
    </div>
  );
}

/* ---- PROTECTED action confirmation ---- */
function ConfirmModal({ data, onClose, onConfirm }) {
  const [ack, setAck] = useState(false);
  const blockedReason = data.blockedReason;
  return (
    <Overlay onClose={onClose} width={540}>
      <ModalHead icon="lock" label="Protected action — confirmation required" title={data.title} onClose={onClose} danger />
      <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 13.5, lineHeight: 1.55, color: 'var(--fg-muted-2)', margin: 0 }}>{data.body}</p>

        <div style={{ border: '1px solid var(--rule)', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: 9 }}>
          <Label size={10}>This will change</Label>
          {data.touches.map((t, i) => (
            <div key={i} style={{ display: 'flex', gap: 9, alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--bad)', marginTop: 1, display: 'flex' }}><Icon name="arrow" size={13} /></span>
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)' }}>{t}</span>
            </div>
          ))}
        </div>

        {data.scriptHint && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Label size={9.5}>Runs</Label>
            <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--accent)' }}>{data.scriptHint}</code>
          </div>
        )}

        {blockedReason ? (
          <div style={{ border: '1px solid var(--bad)', borderLeft: '3px solid var(--bad)', padding: '11px 14px',
            background: 'color-mix(in srgb, var(--bad) 8%, transparent)', display: 'flex', gap: 9 }}>
            <span style={{ color: 'var(--bad)', display: 'flex', flexShrink: 0 }}><Icon name="alert" size={16} /></span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)', lineHeight: 1.5 }}>{blockedReason}</span>
          </div>
        ) : (
          <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start', cursor: 'pointer', userSelect: 'none' }}>
            <span onClick={() => setAck(!ack)} style={{ width: 18, height: 18, border: '1px solid ' + (ack ? 'var(--accent)' : 'var(--fg-muted)'),
              background: ack ? 'var(--accent)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, marginTop: 1 }}>
              {ack && <Icon name="check" size={13} color="var(--accent-ink)" />}
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg-muted-2)', lineHeight: 1.5 }} onClick={() => setAck(!ack)}>
              I, Mike, approve this action. It will be recorded as an explicit approval in the local activity log.
            </span>
          </label>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '16px 22px', borderTop: '1px solid var(--rule)' }}>
        <Btn variant="default" onClick={onClose}>Cancel</Btn>
        {blockedReason ? (
          <Btn variant="default" disabled>Blocked</Btn>
        ) : (
          <button className="nb-confirm" disabled={!ack} onClick={() => { onConfirm(); }}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: ack ? 'pointer' : 'not-allowed',
              fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600,
              padding: '8px 16px', border: '1px solid var(--bad)', color: ack ? 'var(--accent-ink)' : 'var(--bad)',
              background: ack ? 'var(--bad)' : 'transparent', opacity: ack ? 1 : 0.5, minHeight: 34 }}>
            <Icon name="lock" size={12} sw={2} /> {data.cta}
          </button>
        )}
      </div>
    </Overlay>
  );
}

/* ---- INTAKE detail ---- */
function IntakeModal({ rec, onClose, act }) {
  const [draft, setDraft] = useState(rec.ack_draft);
  return (
    <Overlay onClose={onClose} width={600}>
      <ModalHead icon="inbox" label={'Intake · ' + rec.id} title={rec.sender_name} onClose={onClose} />
      <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
          <Meta k="Venue" v={rec.venue} />
          <Meta k="City" v={rec.city} />
          <Meta k="Date" v={rec.date ? fmtDate(rec.date) : 'Not stated'} vColor={rec.date ? null : 'var(--bad)'} nowrap />
          <Meta k="Time" v={rec.time ? fmtTime(rec.time) : 'Not stated'} vColor={rec.time ? null : 'var(--bad)'} nowrap />
          <Meta k="Sender" v={rec.sender} />
          <Meta k="Received" v={fmtClock(rec.received)} nowrap />
        </div>

        <div>
          <Label size={10} style={{ display: 'block', marginBottom: 7 }}>Parsed request</Label>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, lineHeight: 1.55, color: 'var(--fg-muted-2)', margin: 0 }}>{rec.summary}</p>
        </div>

        {rec.missing.length > 0 && (
          <div style={{ border: '1px solid var(--warn)', borderLeft: '3px solid var(--warn)', padding: '11px 14px',
            background: 'color-mix(in srgb, var(--warn) 7%, transparent)' }}>
            <Label size={10} color="var(--warn)" style={{ display: 'block', marginBottom: 6 }}>Missing fields — needed before calendar</Label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
              {rec.missing.map((m, i) => (
                <span key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--fg)',
                  border: '1px solid var(--warn)', padding: '4px 9px', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{m}</span>
              ))}
            </div>
          </div>
        )}

        <div>
          <Label size={10} style={{ display: 'block', marginBottom: 7 }}>Acknowledgment draft — local, not sent</Label>
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={4}
            style={{ width: '100%', boxSizing: 'border-box', background: 'var(--bg)', color: 'var(--fg)',
              border: '1px solid var(--rule)', borderRadius: 0, padding: '11px 13px', fontFamily: 'var(--font-body)',
              fontSize: 13, lineHeight: 1.5, resize: 'vertical' }} />
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '16px 22px', borderTop: '1px solid var(--rule)', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap' }}>
          <Btn icon="check-doc" onClick={() => act('create_receipt', rec)}>Create receipt</Btn>
          <Btn icon="mail" onClick={() => act('draft_email', rec)}>Draft reply</Btn>
          <Btn icon="check" onClick={() => act('mark_reviewed', rec)}>Mark reviewed</Btn>
        </div>
        <ProtectedBtn icon="calendar" onClick={() => act('add_to_calendar', rec)}>Add to Google Calendar</ProtectedBtn>
      </div>
    </Overlay>
  );
}

/* ---- POST-GIG money form ---- */
function MoneyModal({ item, onClose, act }) {
  const [f, setF] = useState({
    base_pay: item.base_pay ?? '', tips: item.tips ?? '', method: item.method ?? 'Cash',
    received_by: item.received_by ?? 'Mike', still_owed: item.still_owed ?? '', notes: item.notes ?? '',
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const field = { width: '100%', boxSizing: 'border-box', background: 'var(--bg)', color: 'var(--fg)',
    border: '1px solid var(--rule)', borderRadius: 0, padding: '9px 11px', fontFamily: 'var(--font-body)', fontSize: 13 };
  const owed = Number(f.still_owed || 0);
  return (
    <Overlay onClose={onClose} width={580}>
      <ModalHead icon="money" label={'Post-gig · ' + item.id} title={item.venue} onClose={onClose} />
      <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', gap: 18 }}>
          <Meta k="Gig date" v={fmtDate(item.date)} />
          <Meta k="City" v={item.city} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          {[['base_pay','Base pay ($)','number'],['tips','Tips ($)','number'],['still_owed','Still owed ($)','number']].map(([k, lab, type]) => (
            <div key={k}>
              <Label size={10} style={{ display: 'block', marginBottom: 6 }}>{lab}</Label>
              <input type={type} value={f[k]} onChange={(e) => set(k, e.target.value)} style={field} placeholder="0" />
            </div>
          ))}
          <div>
            <Label size={10} style={{ display: 'block', marginBottom: 6 }}>Payment method</Label>
            <select value={f.method} onChange={(e) => set('method', e.target.value)} style={field}>
              {['Cash','Check','Venmo','Zelle','Bank transfer','Other'].map((m) => <option key={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <Label size={10} style={{ display: 'block', marginBottom: 6 }}>Received by</Label>
            <input value={f.received_by} onChange={(e) => set('received_by', e.target.value)} style={field} />
          </div>
        </div>
        <div>
          <Label size={10} style={{ display: 'block', marginBottom: 6 }}>Notes</Label>
          <textarea value={f.notes} onChange={(e) => set('notes', e.target.value)} rows={2} style={{ ...field, resize: 'vertical', lineHeight: 1.5 }} />
        </div>
        {owed > 0 && (
          <div style={{ display: 'flex', gap: 9, alignItems: 'center', border: '1px solid var(--warn)', borderLeft: '3px solid var(--warn)',
            padding: '10px 13px', background: 'color-mix(in srgb, var(--warn) 7%, transparent)' }}>
            <span style={{ color: 'var(--warn)', display: 'flex' }}><Icon name="alert" size={15} /></span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)' }}>${owed} still owed — cannot mark payment complete until balance is $0.</span>
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '16px 22px', borderTop: '1px solid var(--rule)', flexWrap: 'wrap' }}>
        <Btn icon="check-doc" onClick={() => act('save_payout', { ...item, ...f })}>Save payout entry (local)</Btn>
        <ProtectedBtn icon="money" onClick={() => act('mark_paid_complete', { ...item, ...f })}>Mark payment complete</ProtectedBtn>
      </div>
    </Overlay>
  );
}

/* ---- DRAFT email composer (safe: creates local/Gmail draft) ---- */
function DraftModal({ ctx, onClose, act, agentmailDown }) {
  const [to, setTo] = useState(ctx.to || '');
  const [subj, setSubj] = useState(ctx.subject || '');
  const [body, setBody] = useState(ctx.body || '');
  const field = { width: '100%', boxSizing: 'border-box', background: 'var(--bg)', color: 'var(--fg)',
    border: '1px solid var(--rule)', borderRadius: 0, padding: '9px 11px', fontFamily: 'var(--font-body)', fontSize: 13 };
  return (
    <Overlay onClose={onClose} width={600}>
      <ModalHead icon="mail" label="Draft email" title={ctx.title || 'New draft'} onClose={onClose} />
      <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 13 }}>
        <div><Label size={10} style={{ display: 'block', marginBottom: 6 }}>To</Label><input value={to} onChange={(e) => setTo(e.target.value)} style={field} /></div>
        <div><Label size={10} style={{ display: 'block', marginBottom: 6 }}>Subject</Label><input value={subj} onChange={(e) => setSubj(e.target.value)} style={field} /></div>
        <div><Label size={10} style={{ display: 'block', marginBottom: 6 }}>Body</Label><textarea value={body} onChange={(e) => setBody(e.target.value)} rows={6} style={{ ...field, resize: 'vertical', lineHeight: 1.55 }} /></div>
        {agentmailDown && (
          <div style={{ display: 'flex', gap: 9, alignItems: 'center', border: '1px solid var(--bad)', borderLeft: '3px solid var(--bad)',
            padding: '10px 13px', background: 'color-mix(in srgb, var(--bad) 8%, transparent)' }}>
            <span style={{ color: 'var(--bad)', display: 'flex' }}><Icon name="alert" size={15} /></span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)' }}>AgentMail is down — direct send is disabled. Saving will create a <b>Gmail draft fallback</b> instead.</span>
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: '16px 22px', borderTop: '1px solid var(--rule)', flexWrap: 'wrap' }}>
        <Btn icon="check-doc" onClick={() => act('save_draft', { to, subj, body, ...ctx })}>Save draft (local)</Btn>
        <ProtectedBtn icon="send" onClick={() => act('send_email', { to, subj, body, ...ctx })}>Send email</ProtectedBtn>
      </div>
    </Overlay>
  );
}

/* ---- per-gig DETAIL ---- */
function GigDetailModal({ gig, data, onClose, H }) {
  const folder = data.venue_folders.find((v) => v.id === gig.folder_id);
  const [terms, setTerms] = useState(gig.pay_terms || '');
  const blocked = gig.status === 'blocked';

  const row = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
    padding: '11px 14px', border: '1px solid var(--rule)' };
  const protLabel = (txt) => <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--fg)' }}>{txt}</span>;

  return (
    <Overlay onClose={onClose} width={640}>
      <ModalHead icon="calendar" label={'Booking · ' + gig.id} title={gig.venue} onClose={onClose} danger={blocked} />
      <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 18 }}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
          border: '1px solid ' + statusColor(gig.status), borderLeft: '3px solid ' + statusColor(gig.status),
          padding: '12px 15px', background: 'color-mix(in srgb, ' + statusColor(gig.status) + ' 8%, transparent)' }}>
          <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)', lineHeight: 1.5 }}>{gig.summary}</span>
          <StatusChip status={gig.status} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px' }}>
          <Meta k="City" v={gig.city} />
          <Meta k="Date" v={fmtDate(gig.date) + ' · ' + fmtTime(gig.time)} nowrap />
          <Meta k="In" v={daysUntil(gig.date, data.meta.now) + ' days'} nowrap />
          <Meta k="Calendar" v={gig.calendar_event ? 'Event exists' : 'None'} nowrap />
          <Meta k="Confirmed" v={gig.confirmed ? 'Yes' : 'Not yet'} vColor={gig.confirmed ? 'var(--ok)' : 'var(--warn)'} nowrap />
          <Meta k="Promo" v={gig.promo_status === 'published' ? 'Flyer published' : gig.promo_status === 'not_started' ? 'Not started' : gig.promo_status} nowrap />
        </div>

        <div>
          <Label size={10} style={{ display: 'block', marginBottom: 8 }}>Verification</Label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
            <CheckDot ok={gig.bandsheet_match} label={gig.bandsheet_match ? 'Band Sheet matches' : 'Band Sheet mismatch'} />
            <CheckDot ok={gig.website_match} label={gig.website_match ? 'Website matches' : 'No website post'} />
            <CheckDot ok={!!folder} label={folder ? 'Folder synced' : 'No folder'} />
            <CheckDot ok={folder && folder.reviewed} label={folder && folder.reviewed ? 'Folder reviewed' : 'Folder unreviewed'} />
          </div>
        </div>

        {gig.logistics.length > 0 && (
          <div style={{ border: '1px solid var(--warn)', borderLeft: '3px solid var(--warn)', padding: '11px 14px',
            background: 'color-mix(in srgb, var(--warn) 7%, transparent)', display: 'flex', flexDirection: 'column', gap: 7 }}>
            <Label size={10} color="var(--warn)">Logistics warnings</Label>
            {gig.logistics.map((l, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--warn)', display: 'flex', marginTop: 1 }}><Icon name="alert" size={13} /></span>
                <span style={{ fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg)', lineHeight: 1.45 }}>{l}</span>
              </div>
            ))}
          </div>
        )}

        <div>
          <Label size={10} style={{ display: 'block', marginBottom: 9 }}>Safe actions — local only</Label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Btn icon="refresh" onClick={() => H.act('run_checks', gig)}>Run checks</Btn>
            <Btn icon="folder" onClick={() => H.act('open_folder', folder || gig)}>Open folder</Btn>
            <Btn icon="mail" onClick={() => H.openDraft({ title: 'Follow-up · ' + gig.venue, subject: 'Neon Blonde — ' + gig.venue + ' ' + fmtDate(gig.date), body: 'Hi — quick follow-up on our ' + fmtDate(gig.date) + ' show…', gigId: gig.id })}>Draft follow-up</Btn>
            <Btn icon="note" onClick={() => H.openNote({ label: gig.venue + ' booking', refId: gig.id })}>Add note</Btn>
          </div>
        </div>

        <div style={{ border: '1px solid var(--rule)', padding: '13px 15px', display: 'flex', flexDirection: 'column', gap: 9 }}>
          <Label size={10}>Pay / rate terms</Label>
          <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap', alignItems: 'center' }}>
            <input value={terms} onChange={(e) => setTerms(e.target.value)} placeholder="e.g. $1,200 guaranteed + bar %"
              style={{ flex: 1, minWidth: 200, boxSizing: 'border-box', background: 'var(--bg)', color: 'var(--fg)',
                border: '1px solid var(--rule)', borderRadius: 0, padding: '9px 11px', fontFamily: 'var(--font-body)', fontSize: 13 }} />
            <ProtectedBtn icon="money" onClick={() => H.act('change_pay_terms', { ...gig, pay_terms: terms })}>Change pay terms</ProtectedBtn>
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <Icon name="lock" size={13} color="var(--bad)" sw={2} />
            <Label size={10} color="var(--bad)">Protected — each requires explicit approval</Label>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={row}>
              {protLabel('Mark booking fully confirmed')}
              <ProtectedBtn icon="check" onClick={() => H.confirmAction({
                title: 'Mark booking fully confirmed', cta: 'Confirm booking',
                body: 'Marks ' + gig.venue + ' (' + fmtDate(gig.date) + ') as fully confirmed across the Band Sheet and internal records.',
                touches: ['Band Sheet: set status = CONFIRMED', 'Internal gig record: lock terms'],
                scriptHint: 'bandsheet_verification_report.py --confirm ' + gig.id,
                blockedReason: blocked ? 'Cannot confirm: an open Band Sheet mismatch must be resolved first.' : null,
                onConfirm: () => H.act('_confirm_booking', gig),
              })}>Confirm</ProtectedBtn>
            </div>
            <div style={row}>
              {protLabel('Publish Band Sheet')}
              <ProtectedBtn icon="sheet" onClick={() => H.act('publish_bandsheet', gig)}>Publish</ProtectedBtn>
            </div>
            <div style={row}>
              {protLabel('Update WordPress show post')}
              <ProtectedBtn icon="globe" onClick={() => H.act('update_wordpress', gig)}>Update</ProtectedBtn>
            </div>
            <div style={row}>
              {protLabel('Share venue portal files')}
              <ProtectedBtn icon="open" onClick={() => H.act('share_portal', gig)}>Share</ProtectedBtn>
            </div>
          </div>
        </div>
      </div>
    </Overlay>
  );
}

/* ---- quick NOTE ---- */
function NoteModal({ ctx, onClose, act }) {
  const [note, setNote] = useState('');
  return (
    <Overlay onClose={onClose} width={480}>
      <ModalHead icon="note" label="Add note" title={ctx.label || 'Note'} onClose={onClose} />
      <div style={{ padding: '20px 22px' }}>
        <textarea autoFocus value={note} onChange={(e) => setNote(e.target.value)} rows={4} placeholder="Local note — saved to the activity log."
          style={{ width: '100%', boxSizing: 'border-box', background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--rule)',
            borderRadius: 0, padding: '11px 13px', fontFamily: 'var(--font-body)', fontSize: 13, lineHeight: 1.5, resize: 'vertical' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '16px 22px', borderTop: '1px solid var(--rule)' }}>
        <Btn variant="default" onClick={onClose}>Cancel</Btn>
        <Btn icon="check-doc" variant="amber" onClick={() => act('add_note', { ...ctx, note })}>Save note</Btn>
      </div>
    </Overlay>
  );
}

Object.assign(window, { Overlay, ModalHead, ConfirmModal, IntakeModal, MoneyModal, DraftModal, NoteModal, GigDetailModal });
