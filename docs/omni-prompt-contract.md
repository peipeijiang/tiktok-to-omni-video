# Omni Flash prompt contract

This project writes text-to-video prompts only. Do not add reference tags, uploaded-media syntax, source URLs, or API keys to the prompt.

## Required order

1. **Technical lock**: 10 seconds, vertical 9:16, 720P, one uncut realistic phone shot.
2. **Evidence-backed inventory**: subject count, identity, clothing or anatomy, relevant props, environment, opening pose, and camera framing.
3. **Causal/comic lock**: the expectation, visible violation, awareness order, reaction, and ending observed in the source.
4. **Motion block**: the measured actor, direction, rate, extension, recoil, stable anchors, and endpoint.
5. **Audio block**: only verified words, sounds, timing, and musical structure.
6. **Continuity lock**: object paths, stable identity, and prohibited drift.

## Fast motion template

```text
[Subject] performs a continuous alternating [left/right limb] extension-and-recoil loop toward [target] at approximately [measured rate] extensions per limb per second. Each limb starts at [guard state], snaps along [visible direction/path], immediately recoils, then hands off to the opposite limb. Keep [stable anchors] stable; only [moving limb] may show narrow directional motion blur. Do not substitute slow waving, held poses, unrelated dancing, or pauses.
```

Use measured values only. If tracking is uncertain because of occlusion or blur, keep the interval uncertain rather than inventing a frequency.
