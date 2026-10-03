# Cached templates during browser checks

- **Trigger:** run a long-lived Django verification server with `--noreload`, then edit templates or Python template tags.
- **Observed:** fresh CSS was served while rendered HTML still used an earlier compiled template. `DEBUG=True` did not make this process a reliable live-edit preview.
- **Impact:** screenshots and height measurements did not represent the current source. A browser reload alone was insufficient.
- **Evidence:** 2026-10-04 visual-redesign verification: the source had removed the range hint, but confirmation HTML still contained it. Restarting the server served current HTML; the eight-player height changed from 1,204 px to 1,177 px.
- **Remedy:** complete the edit batch, restart a verification server without autoreload, then capture. Validate the rendered markup against the source before treating the capture as evidence. Use the normal autoreloading server for development.
