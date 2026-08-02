---
name: telegram-media-delivery
description: Generate, validate, and deliver Telegram media with special handling for animated GIF compatibility and MP4 fallbacks.
---

# Telegram Media Delivery

Use this class skill whenever a user asks for an image, GIF, video, or other local/generated media to be sent through Telegram, especially when animation or client playback matters.

## Workflow

1. **Create or locate the artifact.** Produce the requested format and keep the output at a known absolute path suitable for media delivery.
2. **Validate before sending.** Confirm the file exists, identify its MIME/container type, and inspect relevant metadata. For GIFs, verify multiple frames plus a nonzero frame rate and duration. A successful file extension alone is not evidence of animation.
3. **Send the requested format.** Use the platform's native media attachment mechanism and identify what was sent without overexplaining.
4. **Separate artifact facts from client behavior.** Local inspection can establish frame count, frame rate, duration, and codec; it cannot establish how the recipient's Telegram client displays or autoplays the media.
5. **Handle static-GIF reports.** Explain that Telegram clients may show an animated GIF as a static preview, require tapping to play, or vary by client/platform. If playback is important, create an MP4 fallback.
6. **Encode the fallback for inline playback.** Use a broadly compatible video pixel format such as `yuv420p` and `-movflags +faststart`. Send the MP4 as an additional attachment rather than claiming the GIF was defective without evidence.
7. **Report honestly.** State what was verified locally and what remains dependent on the recipient's app. Do not claim successful playback merely because the file was delivered.

## Verification examples

- GIF inspection: `ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,nb_frames,r_frame_rate,duration -of default=noprint_wrappers=1 file.gif`
- MP4 fallback: `ffmpeg -y -framerate FPS -i frames/frame_%02d.ppm -vf format=yuv420p -movflags +faststart output.mp4`

## Pitfalls

- Do not send a technical test pattern when the user asked for a themed image; create a recognizable subject or ask only when the requested subject is genuinely ambiguous.
- Do not infer that a static preview means the GIF has one frame.
- Do not describe unverified visual details; inspect the artifact first when the user asks for an explanation.
- Avoid unnecessarily long explanations for a simple media request; lead with the attachment and keep diagnostics concise.

## Reference

See `references/telegram-media-delivery.md` for the compact validation and fallback checklist.
