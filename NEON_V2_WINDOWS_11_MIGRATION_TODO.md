# Neon V2 Windows 11 Migration To-Do

## Goal

Move the Neon V2 repository, Python scripts, automations, Telegram bot, skill,
and supporting data from the Mac Mini to the networked Windows 11 machine once
the system is stable and has been used successfully several times.

The Windows 11 machine will become the primary Neon V2 host. It has an Intel
i9 processor, an AMD Radeon RX 6600, attached storage, and a local Gemma model.

## Keep in Mind During Current Development

- Avoid new dependencies on macOS-only tools.
- Keep paths configurable instead of hard-coding `/Volumes/VADER` or `/Users`.
- Store credentials and machine-specific settings outside committed code.
- Keep Python dependencies documented in one reproducible environment file.
- Separate the automation logic from macOS LaunchAgent configuration.
- Prefer cross-platform Python libraries and standard file formats.
- Document every background process, its schedule, inputs, outputs, and logs.
- Keep Google Calendar, Band Sheet, WordPress, email, and Telegram integrations
  independently testable.

## Migration Checklist

- [ ] Finish stabilizing Neon V2 on the Mac Mini.
- [ ] Use the complete workflow several times and resolve remaining problems.
- [ ] Make a final inventory of scripts, bots, automations, data, credentials,
      logs, and external integrations.
- [ ] Back up the repository and all operational data.
- [ ] Install Git, Python, and required command-line tools on Windows 11.
- [ ] Clone or copy the Neon V2 repository to the Windows machine.
- [ ] Create a Windows Python virtual environment.
- [ ] Install and verify all Python dependencies.
- [ ] Replace hard-coded macOS paths with Windows configuration values.
- [ ] Transfer secrets securely and verify account access without committing
      credentials to Git.
- [ ] Replace macOS LaunchAgents with Windows Task Scheduler tasks or Windows
      services.
- [ ] Configure automatic startup after a reboot.
- [ ] Configure persistent logs and failure notifications.
- [ ] Test Band Sheet and spreadsheet reads and writes.
- [ ] Test Google Calendar access and calendar comparison.
- [ ] Test WordPress website checks and updates.
- [ ] Test Telegram bot commands and post-gig payout capture.
- [ ] Test post-gig reminder emails to Mike and Alfred.
- [ ] Test local Gemma integration separately from core Neon V2 automation.
- [ ] Verify network access to all required attached drives and shared folders.
- [ ] Run the Mac and Windows systems in parallel temporarily.
- [ ] Confirm the Windows results match the Mac results.
- [ ] Disable Mac automations before enabling Windows production automations to
      prevent duplicate messages, emails, or spreadsheet writes.
- [ ] Document recovery, restart, update, and rollback procedures.
- [ ] Keep a final Mac backup until the Windows host has run reliably.

## Windows Hosting Decisions to Make Later

- Repository and operational-data locations on the Windows drives.
- Windows Task Scheduler versus long-running Windows services.
- Python version and environment-management method.
- Log storage and retention.
- Backup destination and schedule.
- Remote administration method.
- Whether the local Gemma model assists Neon V2 or remains an optional,
  isolated service.
- How Windows drive letters and network shares map to configurable paths.

## Completion Standard

The migration is complete when the Windows 11 machine can reboot unattended,
start every required Neon V2 process, perform scheduled checks, update approved
data, send Telegram and email notifications, and recover cleanly from temporary
network or API failures without relying on the Mac Mini.
