/* ============================================================
   Neon V2 — Operations Dashboard · mock data
   Internal supervised ops data for Mike. NOT public.
   All objects are local/mock; nothing here is synced live.
   Failure states deliberately seeded:
     - AgentMail health check: DOWN  -> email lane blocked
     - Local model: OFFLINE          -> digest skipped, folders still OK
     - Band Sheet check: MISMATCH     -> publish/trust blocked
     - One venue folder freshly made   -> needs_review
   ============================================================ */
(function () {
  // "now" for the mock — Tue Jun 9, 2026, 04:11 local
  const NOW = '2026-06-09T04:11:00';

  const NEON = {
    meta: {
      now: NOW,
      band: 'Neon Blonde',
      operator: 'Mike',
      project_path: '/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2',
      venues_path: '/Volumes/VADER/Manifold/Neon_Blonde/Venues',
      calendar_url: 'https://calendar.google.com/calendar/u/0/r',
      bandsheet_url: '/Volumes/VADER/Manifold/Neon_Blonde/band_sheet.json',
      last_full_sync: '2026-06-09T03:52:00', // calendar sync
    },

    /* 1 — INTAKE: booking emails parsed BEFORE a calendar entry exists */
    intake_receipts: [
      {
        id: 'INT-2607',
        status: 'needs_review',
        received: '2026-06-09T02:14:00',
        sender: 'booking@thesirenmorrobay.com',
        sender_name: 'The Siren — Morro Bay',
        venue: 'The Siren',
        city: 'Morro Bay, CA',
        date: '2026-07-18',
        time: '21:00',
        parsed: { venue: true, city: true, date: true, time: true, pay: false, load_in: false },
        missing: ['Pay terms', 'Load-in time'],
        summary: 'Asking if Neon Blonde can play Fri Jul 18. 9pm start, two 60-min sets. No pay or load-in stated.',
        ack_draft: 'Hi — thanks for thinking of Neon Blonde for Fri Jul 18. We can hold the date. Before we confirm, can you share the load-in time and the pay/terms? We carry a 6-piece backline. — Mike, Neon Blonde',
        receipt_file: '/Venues/_intake/INT-2607_the-siren_2026-07-18.md',
      },
      {
        id: 'INT-2611',
        status: 'needs_review',
        received: '2026-06-09T03:40:00',
        sender: 'events@coldspringtavern.com',
        sender_name: 'Cold Spring Tavern',
        venue: 'Cold Spring Tavern',
        city: 'Santa Barbara, CA',
        date: null,
        time: null,
        parsed: { venue: true, city: true, date: false, time: false, pay: false, load_in: false },
        missing: ['Specific date', 'Set time', 'Pay terms', 'Load-in time'],
        summary: 'Wants "a Saturday in August" for the patio series. No firm date, time, or pay yet.',
        ack_draft: 'Hi — appreciate the invite for the August patio series. Which Saturday are you targeting? Once we have a date and set time we can check availability and talk terms. — Mike, Neon Blonde',
        receipt_file: '/Venues/_intake/INT-2611_cold-spring-tavern_aug.md',
      },
      {
        id: 'INT-2598',
        status: 'reviewed',
        received: '2026-06-07T18:02:00',
        sender: 'talent@discoveryventura.com',
        sender_name: 'Discovery Ventura',
        venue: 'Discovery Ventura',
        city: 'Ventura, CA',
        date: '2026-07-25',
        time: '20:00',
        parsed: { venue: true, city: true, date: true, time: true, pay: true, load_in: true },
        missing: [],
        summary: 'Reviewed & promoted to calendar. Now tracked in Booking lane (GIG-0419).',
        ack_draft: 'Confirmed receipt — see you Jul 25. — Mike',
        receipt_file: '/Venues/_intake/INT-2598_discovery-ventura_2026-07-25.md',
      },
    ],

    /* 2 — BOOKING: a calendar event exists for these */
    gigs: [
      {
        id: 'GIG-0411',
        status: 'success',
        venue: 'SLO Brew Rock',
        city: 'San Luis Obispo, CA',
        date: '2026-06-20',
        time: '20:00',
        calendar_event: true,
        folder_id: 'VF-SLOBREW',
        bandsheet_match: true,
        website_match: true,
        promo_status: 'published',
        confirmed: true,
        logistics: [],
        summary: 'All checks green. Folder synced, Band Sheet + website agree, flyer published.',
      },
      {
        id: 'GIG-0414',
        status: 'blocked',
        venue: 'BarrelHouse Brewing',
        city: 'Paso Robles, CA',
        date: '2026-06-27',
        time: '19:00',
        calendar_event: true,
        folder_id: 'VF-BARREL',
        bandsheet_match: false,
        website_match: true,
        promo_status: 'published',
        confirmed: false,
        logistics: ['Band Sheet says 8:00 PM, calendar says 7:00 PM — resolve before publishing.'],
        summary: 'Band Sheet ↔ calendar time mismatch. Publishing / "fully confirmed" is blocked until resolved.',
      },
      {
        id: 'GIG-0417',
        status: 'needs_review',
        venue: 'Tooth & Nail Winery',
        city: 'Paso Robles, CA',
        date: '2026-07-11',
        time: '18:00',
        calendar_event: true,
        folder_id: 'VF-TOOTHNAIL',
        bandsheet_match: true,
        website_match: false,
        promo_status: 'not_started',
        confirmed: false,
        logistics: ['New venue — verify contact name & W-9 before deposit.'],
        summary: 'Freshly created venue folder. Verify venue name/contact/date. Website post not up yet; flyer not started.',
      },
      {
        id: 'GIG-0419',
        status: 'needs_review',
        venue: 'Discovery Ventura',
        city: 'Ventura, CA',
        date: '2026-07-25',
        time: '20:00',
        calendar_event: true,
        folder_id: 'VF-DISCOVERY',
        bandsheet_match: true,
        website_match: true,
        promo_status: 'not_started',
        confirmed: false,
        logistics: ['6-piece backline on a small stage — confirm power & stage depth.'],
        summary: 'Checks agree but flyer not started and a logistics warning is open.',
      },
    ],

    /* 3 — LOCAL VENUE FOLDERS under /Venues/[Venue]/[Venue - YYYY-MM-DD]/ */
    venue_folders: [
      { id: 'VF-SLOBREW', status: 'success', venue: 'SLO Brew Rock', date: '2026-06-20', path: '/Venues/SLO Brew Rock/SLO Brew Rock - 2026-06-20/', receipt: true, digest: true, reviewed: true, note: 'Synced. LOCAL_GIG_RECEIPT.md + digest present. Reviewed.' },
      { id: 'VF-BARREL', status: 'success', venue: 'BarrelHouse Brewing', date: '2026-06-27', path: '/Venues/BarrelHouse Brewing/BarrelHouse Brewing - 2026-06-27/', receipt: true, digest: true, reviewed: true, note: 'Synced. Receipt reviewed.' },
      { id: 'VF-TOOTHNAIL', status: 'needs_review', venue: 'Tooth & Nail Winery', date: '2026-07-11', path: '/Venues/Tooth & Nail Winery/Tooth & Nail Winery - 2026-07-11/', receipt: true, digest: false, reviewed: false, note: 'NEW folder — created 02:31. Digest skipped (local model offline). Verify venue name/contact/date.' },
      { id: 'VF-DISCOVERY', status: 'success', venue: 'Discovery Ventura', date: '2026-07-25', path: '/Venues/Discovery Ventura/Discovery Ventura - 2026-07-25/', receipt: true, digest: true, reviewed: true, note: 'Synced & reviewed.' },
      { id: 'VF-MAVERICK', status: 'success', venue: 'The Maverick Saloon', date: '2026-05-30', path: '/Venues/The Maverick Saloon/The Maverick Saloon - 2026-05-30/', receipt: true, digest: true, reviewed: true, note: 'Past gig. Folder retained for records.' },
    ],

    /* 4 — ACCURACY CHECKS (script outputs) */
    checks: [
      {
        id: 'CHK-BANDSHEET',
        kind: 'bandsheet',
        title: 'Band Sheet verification',
        script: 'scripts/bandsheet_verification_report.py',
        status: 'blocked',
        last_run: '2026-06-09T03:48:00',
        result: '1 mismatch — BarrelHouse Brewing (Jun 27): calendar 7:00 PM vs Band Sheet 8:00 PM.',
        detail: 'Compares public Google Calendar against published private Band Sheet JSON. Publishing & "fully confirmed" gated until resolved.',
        affected: ['GIG-0414'],
      },
      {
        id: 'CHK-WEBSITE',
        kind: 'website',
        title: 'Website verification',
        script: 'scripts/website_verification_report.py',
        status: 'needs_review',
        last_run: '2026-06-09T03:49:00',
        result: '1 gap — Tooth & Nail (Jul 11) has no WordPress show post yet.',
        detail: 'Compares public WordPress show posts against the Band Sheet. Gap is expected for an unannounced show.',
        affected: ['GIG-0417'],
      },
    ],

    /* 5 — POST-GIG MONEY (gig date passed) */
    post_gig_items: [
      {
        id: 'PG-0402',
        status: 'pending',
        venue: 'The Maverick Saloon',
        city: 'Santa Ynez, CA',
        date: '2026-05-30',
        base_pay: null,
        tips: null,
        method: null,
        received_by: null,
        still_owed: null,
        paid_complete: false,
        notes: '',
        summary: 'Gig played 10 days ago. No payout entry yet — needs base pay, tips, method.',
      },
      {
        id: 'PG-0405',
        status: 'needs_review',
        venue: 'Ojai Underground Exchange',
        city: 'Ojai, CA',
        date: '2026-06-06',
        base_pay: 800,
        tips: 240,
        method: 'Check',
        received_by: 'Mike',
        still_owed: 150,
        paid_complete: false,
        notes: 'Base + tips received. $150 deposit balance still owed per contract.',
        summary: 'Partial: base + tips in, $150 balance outstanding. Do not mark complete until balance clears.',
      },
    ],

    /* 6 — AGENT STATUS (health, no sends) */
    agent_status: [
      { id: 'AS-AGENTMAIL', key: 'agentmail', title: 'AgentMail', status: 'blocked', script: 'scripts/agentmail_health_check.py', last_check: '2026-06-09T04:02:00', message: 'Health check FAILED — API auth error (401). Outbound send disabled. Gmail draft fallback still available.', blocks: 'Send email' },
      { id: 'AS-INBOX', key: 'inbox', title: 'Inbox monitor', status: 'success', script: 'scripts/monitor_inbox.py', last_check: '2026-06-09T03:55:00', message: 'Running. 2 new intake receipts written since last review.', blocks: null },
      { id: 'AS-CALENDAR', key: 'calendar', title: 'Calendar sync (read)', status: 'success', script: 'local_venue_folder_sync.py --sync-calendar', last_check: '2026-06-09T03:52:00', message: 'Read-only pull OK. 4 upcoming events tracked. No writes performed.', blocks: null },
    ],

    /* 7 — LOCAL MODEL DIGEST */
    local_model_digest: {
      status: 'blocked',
      title: 'Local model',
      model: 'llama-local (Vader)',
      last_ok: '2026-06-08T22:10:00',
      message: 'Local model OFFLINE. Folder creation still succeeds; one-time LOCAL_MODEL_DIGEST.md was skipped for new folders. Re-run digest when model is back.',
      pending_digests: ['VF-TOOTHNAIL'],
    },

    /* 8 — SCOUT AGENT / LEADS (potential new venues) */
    scout_leads: [
      { id: 'SCT-31', status: 'needs_review', venue: 'Pozo Saloon', city: 'Santa Margarita, CA', signal: 'Posted an open Saturday in Sept; books regional 80s/alt acts. Outdoor stage fits 6-piece.', found: '2026-06-09T01:20:00', fit: 'High' },
      { id: 'SCT-29', status: 'needs_review', venue: 'The Ventura Music Hall', city: 'Ventura, CA', signal: 'Mid-size room added a "decades night" series. No cover-band on the Oct calendar yet.', found: '2026-06-08T23:05:00', fit: 'Medium' },
      { id: 'SCT-27', status: 'pending', venue: 'Tooth & Nail (2nd date)', city: 'Paso Robles, CA', signal: 'Already booking Jul 11 — they hinted at a fall repeat. Low effort follow-up.', found: '2026-06-08T20:40:00', fit: 'High' },
    ],
  };

  window.NEON_DATA = NEON;
})();
