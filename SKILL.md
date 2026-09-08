---
name: tiktok-to-omni-video
description: Analyze supplied TikTok videos deeply—including local-Whisper speech transcription, background-music and sound timing, full-video narrative logic, causality, pranks, comedic mechanisms, and audience payoff—and turn them into checked English Omni Flash text-to-video prompts and sequential renders. Use when the user provides TikTok URLs or video files and asks for video breakdowns, faithful replication, cat/dog creative transfer, humorous prompt improvement, audio-aware analysis, generation, retries, or Desktop video outputs.
---

# TikTok to Omni Video

Analyze public TikTok clips from evidence, reconstruct their logic and emotion, write controllable English prompts, compare prompts against the source, and optionally generate 10-second 9:16 Omni Flash videos.

## Non-negotiable operating rules

- Treat every supplied URL as a separate clip and preserve the user’s order. Parse every URL, including the final line; report the exact count and any skipped or unreadable item.
- Use `watch` to download metadata, captions, video, and frames. If the platform route or CLI is unavailable, state the fallback. Never invent unseen actions, dialogue, or objects.
- Extract and inspect the complete audio track whenever technically available. Run the bundled local-audio analyzer; prefer the user's on-device MLX Whisper and automatically fall back to a configured local `whisper.cpp` installation before any cloud transcription route. Treat audio as first-class evidence: obtain timestamped speech, pauses, vocal delivery, background-music presence and structural changes, silence, laughter, impacts, and other sound effects. If audio cannot be extracted or interpreted, state the limitation and downgrade any audio-dependent claim from exact recreation to visual approximation.
- Treat fast repeated motion as first-class evidence. `watch` establishes story, framing, subjects, and action meaning; it is not sufficient to measure a rapid gesture. For any action whose cadence affects the joke or fidelity, analyze the original at native frame rate with tracked points, then carry the measured motion contract into the Omni prompt and use the same measurements to QA the returned video.
- Use T2V only: no reference-image/video tags or upload instructions inside prompts.
- Write all prompts in English.
- Every output is exactly 10 seconds, vertical 9:16, 720P, one continuous uncut shot, realistic phone-captured quality rather than ultra-HD or polished cinema, with natural exposure and motion blur.
- Save successful videos under `/Users/<user>/Desktop/wibly-videos` unless the user specifies another Desktop folder.
- Never claim a video exists until its result has been downloaded and basic duration, container, and dimensions checks pass.
- When the user asks to analyze, replicate, or generate from a clip, show the user the reconstructed overall logic and the complete generated English prompt in the response. Do not hide the reasoning in an internal artifact only. If a prompt artifact is also saved, the response must still include the prompt text or a clearly labeled per-clip prompt block.
- Preserve the source video's causal and entertainment logic exactly. Do not flatten a prank, bait, fake-out, teasing exchange, awkward pause, escalation, reaction, or punchline into a generic “funny” action. Harmless mischief and absurdity are fidelity-critical evidence, not optional decoration.

## Prompt mode selection

- By default, produce two prompts per source: `exact_recreation` and `creative_transfer`.
- If the user says “只要复刻/不要创意迁移/纯复刻”, produce exact prompts only. For subsets such as “前 30 条” or “最后 30 条”, interpret the range by URL order, not by generated-file order. If the user replaces excluded items, preserve the resulting explicit list exactly.
- `exact_recreation` must preserve the original animal/object identity, opening composition, environment, camera behavior, action order, timing, absurdity, emotional curve, and ending state. Do not replace the animal.
- `creative_transfer` may replace only the requested main animal/object, preferably with a small cat or dog when coherent; it must preserve the same comic mechanism, timing, camera, emotional reversal, and endpoint.
- If the user asks only for prompts, do not submit generation jobs. If the user asks to generate, use the latest approved prompt file and the key supplied for that request.

## Evidence-first source analysis

For each clip, produce an internal evidence row before writing the prompt:

1. source index and platform video ID;
2. opening frame: camera height, framing, location, light, subject pose;
3. fixed inventory: every animal/person/prop, count, color, clothing, material, and initial position;
4. action causality: actor, action, force, contact, visible consequence, and endpoint;
5. emotional timeline: baseline emotion, trigger, escalation, realization or misread, peak reaction, and final emotional state;
6. comic mechanism: absurd premise, insult, bait, failed plan, disproportion, awkward pause, overreaction, or illogical payoff;
7. camera behavior, sound/captions if actually available, and visible physics;
8. source-to-prompt audit and any repair made.

### Mandatory audio and audio-visual alignment pass

#### Local Whisper and full-track audio workflow

For every downloaded or local clip with an audio stream, run:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/tiktok-to-omni-video}"
python3 "$SKILL_DIR/scripts/analyze_local_audio.py" "<local-video-path>" --out-dir "<per-clip-audio-dir>"
```

The script must use a configured on-device model and must not upload audio. It first resolves MLX Whisper from `LOCAL_WHISPER_BIN`, `PATH`, and `~/Library/Python/*/bin/mlx_whisper`, using `LOCAL_WHISPER_MODEL` or `~/.cache/watch/whisper-small-mlx`. If that pair is unavailable, it falls back to `whisper-cli` from `WHISPER_CPP_BIN` or `PATH`, using `WHISPER_CPP_MODEL` or `~/.cache/whisper.cpp/ggml-base.bin`. Run `--check` before a batch and stop with a clear remediation message only if neither local backend is ready or `ffmpeg`/`ffprobe` is unavailable.

Treat the generated artifacts as complementary evidence:

- `transcript.json`: timestamped Whisper segments and words; use for spoken content, not speaker identity or non-speech sounds.
- `full_mix.wav`: the complete source mix; inspect it for voice delivery, laughter, background music, effects, silence, and timing.
- `spectrogram.png` and `waveform.png`: inspect sustained harmonic/rhythmic beds, music starts/stops/drops, impacts, energy changes, and silence candidates.
- `audio_analysis.json`: use the timed energy and spectral measurements to locate candidate changes, then verify them against the full mix and visible action. Measurements alone do not prove a song, genre, instrument, emotion, or sound source.

Whisper is the speech evidence layer, not a background-music classifier. Never use transcript gaps as proof of silence or music. Do not name a song, lyric, genre, instrument, or sound source unless it is actually audible/identifiable and visually or contextually supported. If the model cannot inspect `full_mix.wav`, report that limitation and use only the transcript plus measured/spectrogram-supported timing; do not claim exact background-music recreation.

For every clip, classify audio dependency as `essential`, `supportive`, or `irrelevant`:

- `essential`: removing the audio makes the story, dialogue, trigger, or punchline unclear;
- `supportive`: the visual story remains understandable, but audio materially improves timing, emotion, or payoff;
- `irrelevant`: audio does not materially affect the meaning.

When audio is available, record:

1. timestamped speech or dialogue transcript;
2. speaker identity only when supported by visible mouth movement, position, or context;
3. tone, volume, delivery, pauses, interruptions, laughter, gasps, shouts, or deadpan timing;
4. music structure, beat changes, silence, drops, and buildups;
5. sound effects and their visible or explicitly supported source;
6. confidence for every transcript, speaker, and sound interpretation.

Use an audio-visual alignment table as a source of truth:

| Time | Visual action | Speech / sound | Awareness, emotion, or comic function |
|---|---|---|---|
| 0–2s | verified visual action | verified speech, sound, or silence | setup or expectation |

Captions are evidence for words only, not proof of delivery, speaker identity, timing, or sound design. Use transcript timestamps, the audio track, and visible action or reaction together. Never infer dialogue, lyrics, sound effects, or emotional meaning from a title, caption, thumbnail, or familiar meme pattern alone.

If audio is unavailable, mark the clip `audio unavailable`, list every audio-dependent uncertainty, and do not invent dialogue, music, laughter, or sound effects. An `exact_recreation` prompt is permitted only when the joke and causal chain remain fully understandable visually, or when the user explicitly accepts a visual-only approximation.

### Mandatory high-temporal-motion pass

When a gesture is fast, cyclic, occluded, contact-sensitive, or central to the payoff, run a separate native-frame-rate analysis after `watch` and before drafting. Do not infer cadence from uniform storyboard frames.

1. Track 2–5 stable points on each active limb or prop through the original. CoTracker exports can be converted with `scripts/cotracker_npz_to_csv.py`; any tracker may supply the documented CSV schema.
2. Run `scripts/build_motion_spec.py` with the left/right point groups and the action axis. It writes a `motion-spec.json` containing extension times, per-paw rate, peak speed, stroke amplitude, pauses, and alternation quality.
3. Treat the JSON as evidence, not as an instruction to copy unseen events. Keep uncertain or invisible intervals marked uncertain.
4. Make the prompt state the actor, movement direction, measured cycle rate, extension-and-recoil path, stable body anchors, and end state. “Fast” or “energetic” alone is not a valid replacement.
5. Run the same analysis on the generated clip. Report source-versus-output rates and pauses. A result that preserves the action category but misses cadence fails motion fidelity.

For the common pet-paw case, the prompt should say that each paw starts near a compact guard, snaps toward the target, immediately recoils, and hands off to the opposite paw at the measured rate. It must distinguish local directional motion blur on the paw from global blur and must forbid slow waving, held poses, and unrelated dance gestures.

Do not reduce a clip to “animal does funny thing.” Identify what the viewer expects, what breaks that expectation, who understands the joke first, and how the final reaction lands. Write emotion as visible performance: freezes, looks toward the trigger, hesitates, hides, overreacts, resumes smugly, or pretends innocence.

## Full-video logic, character, and emotion pass

Analyze the entire clip as a causal micro-story before drafting any prompt. Do not infer a character, action, relationship, or emotional state solely from a title, caption, thumbnail, or familiar meme pattern.

For each clip, create a structured analysis with these fields:

1. **Premise and viewer contract**: what the first frame makes the viewer expect, the normal rule of the scene, and the question the clip sets up.
2. **Character census**: total number of visible people and animals; for each, assign a stable label (`Person A`, `Dog B`, `Cat C`), describe appearance/pose, role, awareness of the situation, and whether the subject enters, exits, or remains visible. Count background subjects separately and never merge two subjects because they look similar.
3. **Prop and state census**: every relevant object, initial owner/position, material, state, movement, contact, transfer, damage or change, and final position. Distinguish visible props from sounds or implied off-screen props.
4. **Beat-by-beat causal chain**: for each beat, record `time range → actor → intention → action → object/contact/force → visible consequence → other characters’ response → new scene state`. The next beat must be explainable by the state created by the previous beat.
5. **Information and awareness map**: state what each character knows at setup, trigger, reversal, peak, and ending. Mark dramatic irony when the viewer or one character understands the joke before another.
6. **Emotion curve**: assign each character a visible baseline, trigger, first response, escalation, realization/misread, peak reaction, recovery, and final state. Use observable behavior rather than unsupported labels: stare, freeze, flinch, hide, recoil, lean in, smirk, seek approval, feign innocence, or resume the original task.
7. **Relationship and power shift**: identify who initiates, controls, misunderstands, gets embarrassed, wins the exchange, or becomes the target. Track reversals rather than assuming the largest or loudest subject is the protagonist.
8. **Comedy architecture**: identify the setup, expectation, violation, timing gap or pause, reaction, escalation, and payoff. Classify the mechanism as deadpan absurdity, bait-and-switch, failed plan, disproportion, awkward silence, visual irony, petty conflict, innocent misunderstanding, overconfidence, or another evidence-supported mechanism.
9. **Ending function**: explain whether the ending is a punchline, reaction shot, reveal, loop, abrupt cutoff, fake resolution, or unresolved escalation, and preserve that function in the prompt.

10. **Scene and spatial-state sequence**: divide the video into every meaningful visual state, including location changes, entry into or exit from a room/area, movement from foreground to background, changes in camera side or height, occlusion and reveal, and a new object or character becoming visible. For each transition record `time → previous state → visible transition → new state → characters/props carried forward`. Distinguish an actual scene change or cut from a continuous-shot camera move, reframing, pan, tilt, push-in, pull-back, or subject movement. Never describe a scene change that the evidence does not show.
11. **Action-order ledger**: number every observable action in exact order, including preparatory movements, pauses, looks, failed attempts, contact, recoil, pursuit, handoff, exit, and the final settling action. For each action record its start/end time, actor, body part or prop used, direction, contact point, immediate consequence, and whether it changes the next action. Do not collapse several actions into a vague verb such as “reacts,” “attacks,” “plays,” or “moves around.”

Use a compact timeline table when reporting analysis:

| Time | Visible state and action | Character awareness/emotion | Causal consequence | Comic function |
|---|---|---|---|---|

If a count, intention, dialogue, or emotional interpretation is uncertain, label it `uncertain` and give the visual evidence or competing interpretations. Never convert uncertainty into a confident prompt detail. For fast or occluded moments, inspect additional frames or the local video before deciding.

### Required analysis pass for faithful reconstruction

Before drafting any prompt, perform this sequence for the whole clip:

1. Watch the full video once for overall narrative and once again for action order and spatial continuity.
2. Extract and inspect at minimum the opening, each apparent action transition, each contact or reveal, the emotional peak, and the final frame. Add dense frames around fast, occluded, or ambiguous movements.
3. Write the numbered action-order ledger and scene/spatial-state sequence above. The ledger is the source of truth for prompt timing; do not infer timing from the caption, title, thumbnail, or a familiar meme.
4. Check continuity across transitions: the same character, prop, clothing, residue, and environment must be traceable from one state to the next. If a subject leaves frame and later returns, record that explicitly instead of treating it as a new subject.
5. Compare the reconstructed sequence against the full video and mark any uncertain beat. If the uncertainty affects the causal joke or endpoint, do not generate a confident exact-recreation prompt; report the limitation and request a clearer source or use an uncertainty note.
6. Compare the audio-visual alignment table against the full audio track. If an essential sound, line, pause, or musical cue is missing or unclear, block exact-recreation generation until the source is clarified or the user accepts a visual-only approximation.

For faithful recreation, preserve the observable action sequence even when it is awkward or inefficient: setup movement → look or hesitation → trigger → contact or failed attempt → consequence → reaction → pursuit/retreat or scene transition → final pose/state. Preserve meaningful pauses and the order of eyelines. If the source contains a cut, the Omni prompt must not invent a cut because the output contract is one continuous shot; instead reproduce the same visible state change with an explicitly described continuous camera move only when that is physically plausible. If it is not plausible, flag the mismatch rather than silently changing the source logic.

### Narrative and entertainment fidelity lock

Before a prompt can pass, compare it directly with the source and verify all of the following:

1. The same normal expectation is established before the disruption.
2. The same initiator performs the same prank, bait, fake-out, failed plan, petty act, or absurd behavior for the same observable reason.
3. Preparatory looks, concealment, hesitation, contact, discovery, delay, escalation, and reaction remain in the original order.
4. The viewer and each character learn the trick or mistake at the same relative moment; preserve dramatic irony and who is “in on it.”
5. The target's reaction, the instigator's reaction, the power reversal, and the final winner/loser or embarrassed party remain unchanged.
6. The same punchline lands through the same visible and audible mechanism, including any pause, musical cue, silence, shout, impact, or abrupt cutoff.
7. No generic replacement joke, nicer behavior, random slapstick, extra escalation, new prop, new character, or alternate ending has displaced the source's hook.

Failure of any item blocks generation until the prompt is repaired. Safety adaptations may make dangerous conduct clearly harmless or simulated, but must preserve the source's non-injurious comic causality, timing, and payoff rather than removing the prank or joke.

### User-visible handoff requirement

The response must expose the reconstruction before any generation job is submitted. Use this order for each clip:

1. `Overall logic`: one concise paragraph explaining setup, expectation, trigger, action chain, reversal, escalation, and endpoint.
2. `Action order and scene changes`: a numbered list or timeline table containing every important action and each verified spatial/camera transition.
3. `Audio evidence and alignment`: audio dependency level, transcript or sound summary, audio-visual timing, and any unavailable or uncertain audio evidence.
4. `Characters, props, awareness, and emotion`: only the evidence-supported census and state changes.
5. `Complete English prompt`: the exact prompt text that will be submitted, in a fenced code block. If both modes are requested, show `exact_recreation` and `creative_transfer` as separate complete blocks.
6. `QA repairs`: list any prompt wording changed to preserve action order, scene continuity, timing, audio alignment, or uncertainty.

Never respond with only a link to a JSON file, a generated video, or a summary such as “the prompt is ready.” The user must be able to inspect the full logic and the exact prompt before generation. When the user asks for generation, show the prompts first, then submit according to the job gate.

## Humor requirement for generated prompts

Make the generated result visibly humorous through situation, timing, and reaction—not through generic adjectives such as “funny,” “hilarious,” or “comedic.” Every prompt must preserve or construct a clear comedic beat:

- establish a normal expectation in the first beat;
- create one legible, harmless violation or misunderstanding;
- hold a brief readable pause, hesitation, or delayed reaction when the source supports it;
- show the exact subject noticing, misreading, overreacting, or pretending innocence;
- land on a specific visual payoff before the endpoint.

Translate humor into actions and camera timing: a smug glance followed by immediate failure, an animal confidently repeating the wrong action, a person trying to stay serious while the situation becomes absurd, an awkward pause before a disproportionate reaction, or a deadpan return to normal. Keep reactions readable and grounded in the source’s logic.

For `exact_recreation`, preserve the source’s actual comic mechanism, order, tone, and endpoint; intensify clarity with pauses, eyelines, reaction framing, and timing only when those changes do not alter the event. For `creative_transfer`, retain the mechanism and emotional reversal while allowing a small, harmless escalation or deadpan reaction that makes the transferred animal/object feel naturally funny. Do not add random slapstick, extra characters, new props, dialogue, captions, or a different punchline.

Add this humor lock to every generated prompt when compatible with the source:

```text
Play the humor through clear cause-and-effect, readable eyelines, a brief reaction pause, and a specific visual punchline. Keep the absurdity harmless and grounded; do not use generic comedy montage, random slapstick, extra characters, laugh-track behavior, or unexplained events. Let the final reaction land visibly before the shot ends.
```

### Frame coverage and uncertainty

- Begin with efficient keyframes, then increase coverage for any unclear action. For a batch, create dense contact sheets for all clips, not just the first few.
- Read every listed frame. For fragile or fast actions, use more frames or inspect the local video directly.
- Build a per-clip transition map from the frames: opening composition, each reframe or camera move, each subject/prop entry or exit, every occlusion/reveal, and the endpoint. A transition may be labeled `not observed` only after checking the relevant interval.
- If a clip lacks video frames, captions, or audio, mark the limitation and do not fill the gap with a generic pet-prank template. Ask for the source or omit it according to the user’s instruction.
- Before finalizing a large prompt set, spot-check opening, every action transition, every scene/spatial transition, trigger, reversal, peak, and endpoint for every clip. Do not let metadata titles substitute for visual evidence.

## Prompt construction contract

Use this order:

`duration/aspect + phone-shot style + exact character/prop inventory + opening visual/audio state + timed audio-visual causal beats + awareness/emotional transition + camera + comic timing/payoff + audio and visual continuity locks`

Every action must name the actor and object, timing, intention, direction/force, visible consequence, affected characters, emotional response, and final state. Use enough timed beats to cover the verified action-order ledger; do not force a dense sequence into only three or four beats. A compact example is `0–2s setup; 2–3s look/hesitation; 3–5s trigger and contact; 5–7s consequence/reversal; 7–10s peak and endpoint`. If the source has a meaningful spatial transition, state exactly how it occurs in the continuous shot: `the phone pans right as Person A crosses the doorway`, `the camera follows Dog B from the kitchen into the hall`, or `the subject remains in the same room while the camera pushes closer`. Never use vague wording such as “the scene changes” without describing the visible transition.

When audio is `essential` or `supportive`, add an explicit audio block to the prompt. Align every important line, pause, background-music start/stop/drop, silence, reaction, and sound effect with the verified visual action that triggers or responds to it. Do not add narration, dialogue, music, laughter, captions, or sound effects unless supported by the source or explicitly requested by the user. Preserve the order `visible trigger → sound or speech → character hears/notices → reaction` when that order is supported by evidence.

For `exact_recreation`, the prompt must contain a one-line `sequence lock` that lists the verified action order and a one-line `spatial lock` that lists the verified environment/camera transitions. These locks are mandatory even when the prompt also contains the general continuity lock below.

Every prompt must include or clearly imply this lock:

```text
10-second vertical 9:16 smartphone video, one continuous uncut shot, realistic ordinary phone quality, not ultra-HD, natural exposure and motion blur. Keep the exact subject count, identity, anatomy, clothing, object count, shape, color, material, and position consistent from first frame to last. Every object must already exist before it moves, travel along a visible physical path, make visible contact, and end in a visible stable state. Nothing suddenly appears, disappears, duplicates, teleports, melts, inflates, shrinks, recolors, changes material, or is replaced off-screen. No morphing, extra limbs, cuts, transitions, scene changes, or unexplained camera jumps.
```

Add a clip-specific continuity ledger for fragile items:

- liquids/foam/powder: name the source, flow path, accumulation, and final residue;
- food/chips/coins: keep each piece separate until visible contact, eating, or gravity changes it;
- bottles/cups/phones: keep them rigid, countable, and visibly transferred;
- cloth/blankets/clothing: keep them attached to the correct subject and physically draped;
- reflections/screens: keep the real object and reflection aligned;
- smoke/explosion/surreal transformations: describe the visible cause and aftermath; do not allow free-floating effects to replace the subject.

Do not sanitize away harmless absurdity, rudeness, illogical cause-and-effect, awkward pauses, exaggerated reactions, or abrupt endings. Keep dangerous action non-injurious and cartoonish.

## Source-to-prompt QA gate

Run this audit for every prompt before generation:

| Check | Pass condition |
|---|---|
| Evidence | Every described beat is supported by frames/video/captions; uncertain details are labeled. |
| Audio evidence | Audio dependency is classified; essential speech, pauses, music cues, and sound effects are transcribed or marked unavailable. |
| Audio-visual alignment | Important sound and speech events align with the visible action and character reaction in source order. |
| Audio limitation | Missing or unintelligible essential audio blocks exact-recreation claims unless the user accepts visual-only approximation. |
| Opening | Location, camera, subject pose, count, and object placement match the source. |
| Census | The prompt preserves the verified number and identity of people, animals, and relevant props. |
| Logic | Trigger, consequence, emotional reversal, peak, and ending occur in the source order. |
| Humor | The exact absurd premise and why it is funny remain visible. |
| Prank/joke fidelity | The setup, deception or violation, awareness timing, escalation, reaction, power shift, and payoff match the source; no substitute joke was introduced. |
| Emotion | Each important character has a visible baseline, response, escalation, and final state. |
| Timing | All actions fit 10 seconds and end in a changed but visible state. |
| Continuity | Every object has an origin, path, contact, and endpoint; no unexplained disappearance. |
| Camera | One phone-camera shot with only source-supported movement. |
| Stability | Faces, paws/hands, animals, fragile props, liquids, and clothing are protected from drift. |
| Exactness | Exact prompts do not replace animals, props, or locations. |
| Transfer | Transfer changes only the named subject/object and retains mechanism and endpoint. |
| Safety | No real animal harm, blood, dangerous stunt, or copied watermark/brand text. |

Repair any failed check. Store the audit beside the prompt artifact when the batch is large.

## Job and submission discipline

Create a temporary JSON job list with one job per prompt. Use stable ASCII-safe IDs such as `source-video-id-exact-v2` and separate exact/transfer jobs. Never put an API key in the job file.

- Maintain a persistent manifest for every POST attempt. Record the job before POSTing so crashes cannot cause a duplicate.
- Never submit the same prompt/job ID twice. A failed, unknown, or timed-out POST is not automatically retried.
- A retry is allowed only when the user explicitly requests it after an external-state change such as recharge, and it must use a new retry job ID while preserving the original failed record.
- Status polling and result downloading may retry without a new POST because they do not create a generation task.
- First-video review gate: after analyzing and checking all requested prompts, submit exactly one new job—the first job in the complete ordered video queue—and then stop. Even if the initial request says to generate all, do not submit the rest before the user reviews this first video.
- After that video's file has downloaded and validation passes, show its exact local file and ask the user to inspect it. Do not submit another job until the user explicitly says `continue`/`继续` in a later turn.
- The first `continue`/`继续` after that review authorizes submission of all remaining unsubmitted jobs in the complete queue. Skip all manifest-recorded success, failed, unknown, and submitted jobs; preserve stable source/prompt order; submit every remaining job with `--all-remaining`; then poll, download, validate, and report all results. Do not ask for confirmation between those remaining jobs.
- If the API returns insufficient balance, rate limit, upstream overload, or Cloudflare errors, report the exact error and stop or record according to the manifest rules; do not silently resubmit.

Use the bundled runner after loading the Omni API reference:

```bash
export OMNI_API_KEY='...'
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/tiktok-to-omni-video}"
python3 "$SKILL_DIR/scripts/generate_omni.py" jobs.json --limit 1
```

Use `--limit 1` before review. Only after the user says `continue`/`继续`, run the same manifest and job list with `--all-remaining`:

```bash
python3 "$SKILL_DIR/scripts/generate_omni.py" jobs.json --all-remaining
```

Do not use `--all-remaining` before the first generated video has been shown to the user and the user has explicitly continued.

## Handoff

Return, in order:

1. source count, order, access caveats, and omitted items;
2. per-clip full-video logic analysis, audio dependency and alignment, character/prop census, awareness map, emotion curve, relationship/power shift, and comic mechanism;
3. English exact and, if requested, transfer prompts;
4. source-to-prompt QA and repairs;
5. submitted, downloaded, failed, unknown, and retry manifest counts;
6. exact Desktop file links.

For prompt-only work, link the prompt artifact and do not imply generation. For generation work, report each successful local file only after validation.

## Resource routing

- Read the installed `watch` skill for TikTok extraction and frame inspection.
- Use `seedance-prompt`, `seedance-motion`, `seedance-camera`, `seedance-characters`, and `prompt-preflight-qa` principles when relevant, even though the final runner is Omni Flash.
- Read the Omni Flash API reference before using the API.
- Use `agent-reach` for platform/internet routing when available; if unavailable, use the installed watch path only when it can access the public URL and state the fallback.

## Safety and rights

Analyze and transform user-supplied public clips. Do not copy creator names, watermarks, readable brand marks, or private-person likenesses. Preserve harmless comedic absurdity without generating real animal abuse, injury, blood, or dangerous stunts.
