/* ============================================================
   Neon V2 — Today strip + the 8 operations panels
   ============================================================ */

/* tiny inline check indicator (Band Sheet / Website agreement) */
function CheckDot({ ok, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{ width: 7, height: 7, background: ok ? 'var(--ok)' : 'var(--bad)', flexShrink: 0 }} />
      <Label size={9.5} ls="0.05em" color={ok ? 'var(--fg-muted-2)' : 'var(--bad)'}>{label}</Label>
    </span>
  );
}

/* ====== TODAY STRIP ====== */
function TodayStrip({ data, H }) {
  const now = data.meta.now;
  const blockers = [];
  data.gigs.forEach((g) => { if (g.status === 'blocked') blockers.push({ t: g.venue + ' — time mismatch', id: g.id }); });
  data.agent_status.forEach((a) => { if (a.status === 'blocked') blockers.push({ t: a.title + ' down', id: a.id }); });
  if (data.local_model_digest.status === 'blocked') blockers.push({ t: 'Local model offline', id: 'LM' });
  data.checks.forEach((c) => { if (c.status === 'blocked') blockers.push({ t: c.title + ' mismatch', id: c.id }); });

  const upcoming = data.gigs.filter((g) => daysUntil(g.date, now) >= 0).sort((a, b) => a.date.localeCompare(b.date));
  const next = upcoming[0];

  // first move = highest-priority blocked item
  const firstMove = data.gigs.find((g) => g.status === 'blocked');

  const cell = { padding: '18px 22px', background: 'var(--surface)', display: 'flex', flexDirection: 'column', gap: 9, minWidth: 0 };
  return (
    <div className="nb-today" style={{ border: '1px solid var(--rule)', borderTop: '3px solid var(--accent)' }}>
      {/* First move */}
      <div style={cell}>
        <Label size={10} color="var(--accent)" ls="0.1em">◉ Today's First Move</Label>
        {firstMove ? (
          <>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.1, color: 'var(--fg)' }}>
              Resolve {firstMove.venue} time mismatch
            </div>
            <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--fg-muted)', lineHeight: 1.45 }}>
              Calendar says {fmtTime(firstMove.time)}, Band Sheet disagrees. Publishing is blocked until resolved.
            </p>
            <div style={{ marginTop: 2 }}>
              <Btn icon="arrow" variant="amber" onClick={() => H.scrollTo('panel-checks')}>Go to Accuracy Checks</Btn>
            </div>
          </>
        ) : (
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 600, color: 'var(--fg)' }}>All lanes clear.</div>
        )}
      </div>
      {/* Next gig */}
      <div style={cell}>
        <Label size={10} ls="0.1em">Next gig</Label>
        {next && (
          <>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600, letterSpacing: '-0.015em', color: 'var(--fg)', lineHeight: 1.1 }}>{next.venue}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: 'var(--accent)', display: 'flex', flexShrink: 0 }}><Icon name="calendar" size={14} /></span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg-muted-2)', lineHeight: 1.35, whiteSpace: 'nowrap' }}>{fmtDate(next.date)} · {fmtTime(next.time)}</span>
            </div>
            <Label size={10} color="var(--accent)">In {daysUntil(next.date, now)} days · {next.city}</Label>
          </>
        )}
      </div>
      {/* Critical blockers */}
      <div style={{ ...cell, background: blockers.length ? 'color-mix(in srgb, var(--bad) 9%, transparent)' : 'transparent' }}>
        <Label size={10} color={blockers.length ? 'var(--bad)' : 'var(--fg-muted)'} ls="0.1em">Critical blockers</Label>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 34, fontWeight: 600, lineHeight: 0.9, color: blockers.length ? 'var(--bad)' : 'var(--ok)' }}>{blockers.length}</span>
          <Label size={10} color="var(--fg-muted)" style={{ whiteSpace: 'nowrap' }}>need attention</Label>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {blockers.slice(0, 3).map((b, i) => (
            <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span style={{ width: 5, height: 5, background: 'var(--bad)', flexShrink: 0 }} />
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)' }}>{b.t}</span>
            </div>
          ))}
        </div>
      </div>
      {/* Last sync */}
      <div style={{ ...cell }}>
        <Label size={10} ls="0.1em">Last successful sync</Label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--ok)', display: 'flex', flexShrink: 0 }}><Icon name="check" size={15} /></span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--fg)', lineHeight: 1.35, whiteSpace: 'nowrap' }}>{fmtClock(data.meta.last_full_sync)}</span>
        </div>
        <Label size={10}>Calendar read · {relTime(data.meta.last_full_sync, now)}</Label>
        <div style={{ marginTop: 2 }}>
          <Btn icon="refresh" onClick={() => H.act('rerun_sync')}>Re-check now</Btn>
        </div>
      </div>
    </div>
  );
}

/* ====== 1 · INTAKE QUEUE ====== */
function IntakeQueue({ data, H, hideClear, compact }) {
  let rows = data.intake_receipts;
  if (hideClear) rows = rows.filter((r) => r.status !== 'reviewed');
  const open = rows.filter((r) => r.status !== 'reviewed').length;
  return (
    <Panel id="intake" title="Intake Queue" icon="inbox" section="§ Phase 1 — pre-calendar" count={open}
      status={open ? 'needs_review' : 'success'} compact={compact}>
      {rows.length === 0 && <Empty label="No intake items" />}
      {rows.map((r) => (
        <Item key={r.id} status={r.status === 'reviewed' ? 'success' : r.status} onClick={() => H.openIntake(r)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{r.venue}</div>
              <Label size={10} style={{ display: 'block', marginTop: 2 }}>{r.city} · {r.date ? fmtDate(r.date) : 'no date'} · {r.id}</Label>
            </div>
            <StatusChip status={r.status === 'reviewed' ? 'reviewed' : r.status} />
          </div>
          {r.missing.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span style={{ color: 'var(--warn)', display: 'flex' }}><Icon name="alert" size={13} /></span>
              <Label size={10} color="var(--fg-muted-2)">{r.missing.length} missing: {r.missing.join(', ')}</Label>
            </div>
          )}
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }} onClick={(e) => e.stopPropagation()}>
            <Btn icon="eye" onClick={() => H.openIntake(r)}>Review</Btn>
            <Btn icon="check-doc" onClick={() => H.act('create_receipt', r)}>Create receipt</Btn>
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ====== 2 · BOOKING / VENUE AGENT QUEUE ====== */
function BookingQueue({ data, H, hideClear, compact }) {
  let rows = data.gigs;
  if (hideClear) rows = rows.filter((g) => g.status !== 'success');
  const worst = rows.reduce((acc, g) => Math.min(acc, statusRank[g.status] ?? 9), 9);
  const pStatus = worst === 0 ? 'blocked' : worst === 1 ? 'needs_review' : 'success';
  return (
    <Panel id="booking" title="Booking Queue" icon="calendar" section="§ Phase 2 — calendar exists" count={data.gigs.length}
      status={pStatus} compact={compact}>
      {rows.map((g) => (
        <Item key={g.id} status={g.status} onClick={() => H.openGig(g)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{g.venue}</div>
              <Label size={10} style={{ display: 'block', marginTop: 2 }}>{g.city} · {fmtDate(g.date)} {fmtTime(g.time)} · in {daysUntil(g.date, data.meta.now)}d</Label>
            </div>
            <StatusChip status={g.status} />
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 14px', alignItems: 'center' }}>
            <CheckDot ok={g.bandsheet_match} label="Band Sheet" />
            <CheckDot ok={g.website_match} label="Website" />
            <CheckDot ok={g.folder_id} label="Folder" />
            <CheckDot ok={g.promo_status === 'published'} label={g.promo_status === 'published' ? 'Flyer' : 'No flyer'} />
          </div>
          {g.logistics.length > 0 && (
            <div style={{ display: 'flex', gap: 7, alignItems: 'flex-start' }}>
              <span style={{ color: g.status === 'blocked' ? 'var(--bad)' : 'var(--warn)', display: 'flex', marginTop: 1 }}><Icon name="alert" size={13} /></span>
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)', lineHeight: 1.45 }}>{g.logistics[0]}</span>
            </div>
          )}
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }} onClick={(e) => e.stopPropagation()}>
            <Btn icon="eye" variant="amber" onClick={() => H.openGig(g)}>Open details</Btn>
            <Btn icon="refresh" onClick={() => H.act('run_checks', g)}>Run checks</Btn>
            <Btn icon="folder" onClick={() => H.act('open_folder', g)}>Open folder</Btn>
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ====== 3 · ACCURACY CHECKS ====== */
function AccuracyChecks({ data, H, compact }) {
  const worst = data.checks.reduce((a, c) => Math.min(a, statusRank[c.status] ?? 9), 9);
  const pStatus = worst === 0 ? 'blocked' : worst === 1 ? 'needs_review' : 'success';
  return (
    <Panel id="checks" title="Accuracy Checks" icon="check-doc" section="§ Verification" status={pStatus} compact={compact}
      headerRight={<Btn icon="refresh" onClick={() => H.act('run_all_checks')}>Run all</Btn>}>
      {data.checks.map((c) => (
        <Item key={c.id} status={c.status}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{c.title}</div>
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--fg-muted)' }}>{c.script}</code>
            </div>
            <StatusChip status={c.status} />
          </div>
          <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--fg-muted-2)', lineHeight: 1.5 }}>{c.result}</p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <Label size={9.5}>Last run {relTime(c.last_run, data.meta.now)}</Label>
            <div style={{ display: 'flex', gap: 7 }}>
              <Btn icon="refresh" onClick={() => H.act(c.kind === 'bandsheet' ? 'run_bandsheet' : 'run_website', c)}>
                Re-run {c.kind === 'bandsheet' ? 'Band Sheet' : 'Website'} check
              </Btn>
              {c.status !== 'success' && <Btn icon="flag" onClick={() => H.openNote({ label: c.title, refId: c.id })}>Add note</Btn>}
            </div>
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ====== 4 · LOCAL VENUE FOLDERS ====== */
function VenueFolders({ data, H, hideClear, compact }) {
  let rows = data.venue_folders;
  if (hideClear) rows = rows.filter((v) => v.status !== 'success');
  const needs = data.venue_folders.filter((v) => v.status === 'needs_review').length;
  return (
    <Panel id="folders" title="Venue Folders" icon="folder" section="§ /Venues" count={data.venue_folders.length}
      status={needs ? 'needs_review' : 'success'} compact={compact}
      headerRight={<Btn icon="plus" onClick={() => H.act('create_folder')}>New folder</Btn>}>
      {rows.map((v) => (
        <Item key={v.id} status={v.status}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{v.venue}</div>
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--fg-muted)', wordBreak: 'break-all' }}>{v.path}</code>
            </div>
            <StatusChip status={v.status} />
          </div>
          <div style={{ display: 'flex', gap: 14 }}>
            <CheckDot ok={v.receipt} label="Receipt" />
            <CheckDot ok={v.digest} label={v.digest ? 'Digest' : 'No digest'} />
            <CheckDot ok={v.reviewed} label={v.reviewed ? 'Reviewed' : 'Unreviewed'} />
          </div>
          <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)', lineHeight: 1.45 }}>{v.note}</p>
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
            <Btn icon="open" onClick={() => H.act('open_folder', v)}>Open in Finder</Btn>
            {!v.reviewed && <Btn icon="check" onClick={() => H.act('mark_folder_reviewed', v)}>Mark receipt reviewed</Btn>}
            {!v.digest && <Btn icon="cpu" onClick={() => H.act('rerun_digest', v)}>Re-run digest</Btn>}
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ====== 5 · POST-GIG MONEY ====== */
function MoneyQueue({ data, H, hideClear, compact }) {
  let rows = data.post_gig_items;
  if (hideClear) rows = rows.filter((p) => !p.paid_complete);
  return (
    <Panel id="money" title="Post-Gig Money" icon="money" section="§ Phase 3 — gig passed" count={rows.length}
      status={rows.some((p) => p.status !== 'success') ? 'needs_review' : 'success'} compact={compact}>
      {rows.length === 0 && <Empty label="No outstanding payouts" />}
      {rows.map((p) => (
        <Item key={p.id} status={p.paid_complete ? 'success' : p.status} onClick={() => H.openMoney(p)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{p.venue}</div>
              <Label size={10} style={{ display: 'block', marginTop: 2 }}>{fmtDate(p.date)} · {p.city}</Label>
            </div>
            <StatusChip status={p.paid_complete ? 'success' : p.status} />
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Stat k="Base" v={p.base_pay != null ? '$' + p.base_pay : '—'} />
            <Stat k="Tips" v={p.tips != null ? '$' + p.tips : '—'} />
            <Stat k="Owed" v={p.still_owed ? '$' + p.still_owed : '$0'} c={p.still_owed ? 'var(--bad)' : 'var(--ok)'} />
            <Stat k="Method" v={p.method || '—'} />
          </div>
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }} onClick={(e) => e.stopPropagation()}>
            <Btn icon="money" variant="amber" onClick={() => H.openMoney(p)}>{p.base_pay == null ? 'Enter payout' : 'Edit payout'}</Btn>
            <Btn icon="note" onClick={() => H.openNote({ label: p.venue + ' payout', refId: p.id })}>Add note</Btn>
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ====== 6 · AGENTMAIL STATUS ====== */
function AgentMailStatus({ data, H, compact }) {
  const am = data.agent_status.find((a) => a.key === 'agentmail');
  return (
    <Panel id="agentmail" title="AgentMail Status" icon="mail" section="§ Email lane" status={am.status} compact={compact}
      headerRight={<Btn icon="refresh" onClick={() => H.act('run_agentmail_health')}>Health check</Btn>}>
      {data.agent_status.map((a) => (
        <div key={a.id} style={{ border: '1px solid var(--rule)', borderLeft: '3px solid ' + statusColor(a.status), padding: '11px 13px',
          background: a.status === 'blocked' ? 'color-mix(in srgb, var(--bad) 6%, transparent)' : 'transparent', display: 'flex', flexDirection: 'column', gap: 7 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 13.5, fontWeight: 600, color: 'var(--fg)' }}>{a.title}</span>
            <StatusChip status={a.status} />
          </div>
          <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)', lineHeight: 1.45 }}>{a.message}</p>
          {a.blocks && <Label size={9.5} color="var(--bad)">Blocks: {a.blocks} (Gmail draft fallback available)</Label>}
        </div>
      ))}
    </Panel>
  );
}

/* ====== 7 · LOCAL MODEL STATUS ====== */
function LocalModelStatus({ data, H, compact }) {
  const lm = data.local_model_digest;
  return (
    <Panel id="localmodel" title="Local Model Status" icon="cpu" section="§ Digest engine" status={lm.status} compact={compact}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 10, height: 10, background: statusColor(lm.status), flexShrink: 0 }} />
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 600, color: 'var(--fg)' }}>{lm.model}</span>
      </div>
      <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 12.5, color: 'var(--fg-muted-2)', lineHeight: 1.5 }}>{lm.message}</p>
      <div style={{ display: 'flex', gap: 18 }}>
        <Meta k="Last OK" v={fmtClock(lm.last_ok) + ' · ' + relTime(lm.last_ok, data.meta.now)} />
        <Meta k="Pending" v={lm.pending_digests.length + ' digest(s)'} vColor="var(--warn)" />
      </div>
      <div style={{ border: '1px solid var(--rule)', borderLeft: '3px solid var(--ok)', padding: '10px 13px', display: 'flex', gap: 9 }}>
        <span style={{ color: 'var(--ok)', display: 'flex' }}><Icon name="check" size={15} /></span>
        <span style={{ fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)', lineHeight: 1.45 }}>Folder creation is unaffected — folders are still made; the digest step is simply skipped and queued.</span>
      </div>
      <div style={{ display: 'flex', gap: 7 }}>
        <Btn icon="refresh" onClick={() => H.act('retry_local_model')}>Retry connection</Btn>
        <Btn icon="cpu" onClick={() => H.act('rerun_digest', { venue: 'queued' })}>Run pending digests</Btn>
      </div>
    </Panel>
  );
}

/* ====== 8 · SCOUT AGENT / LEADS ====== */
function ScoutLeads({ data, H, hideClear, compact }) {
  let rows = data.scout_leads;
  return (
    <Panel id="scout" title="Scout / Leads" icon="scout" section="§ Prospecting" count={rows.length}
      status="needs_review" compact={compact}>
      {rows.map((s) => (
        <Item key={s.id} status={s.status}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--fg)' }}>{s.venue}</div>
              <Label size={10} style={{ display: 'block', marginTop: 2 }}>{s.city} · fit {s.fit} · found {relTime(s.found, data.meta.now)}</Label>
            </div>
            <StatusChip status={s.status} />
          </div>
          <p style={{ margin: 0, fontFamily: 'var(--font-body)', fontSize: 11.5, color: 'var(--fg-muted-2)', lineHeight: 1.45 }}>{s.signal}</p>
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
            <Btn icon="mail" onClick={() => H.openDraft({ title: 'Outreach · ' + s.venue, subject: 'Neon Blonde — booking inquiry', body: 'Hi — Neon Blonde is a 6-piece 80s post-punk cover band on the Central Coast. We saw you book decades/80s acts and wanted to ask about open dates…' })}>Draft outreach</Btn>
            <Btn icon="note" onClick={() => H.openNote({ label: s.venue + ' lead', refId: s.id })}>Add note</Btn>
            <Btn icon="check" onClick={() => H.act('mark_lead_reviewed', s)}>Mark reviewed</Btn>
          </div>
        </Item>
      ))}
    </Panel>
  );
}

/* ---- tiny helpers ---- */
function Stat({ k, v, c }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Label size={9} ls="0.06em">{k}</Label>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 500, color: c || 'var(--fg)' }}>{v}</span>
    </div>
  );
}
function Empty({ label }) {
  return (
    <div style={{ padding: '18px 0', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
      <span style={{ color: 'var(--ok)', display: 'flex' }}><Icon name="check" size={20} /></span>
      <Label size={10}>{label}</Label>
    </div>
  );
}

Object.assign(window, {
  TodayStrip, IntakeQueue, BookingQueue, AccuracyChecks, VenueFolders,
  MoneyQueue, AgentMailStatus, LocalModelStatus, ScoutLeads, CheckDot, Stat, Empty,
});
