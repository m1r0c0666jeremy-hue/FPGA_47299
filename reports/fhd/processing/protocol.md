# Native 1080p processing interface

The active protocol is version 5 (`fhd_metadata.vh`). The candidate, result,
and display snapshot remain 128, 768, and 852 bits respectively. Version 4
consumers must reject these packets.

Candidate fields, low to high: bbox 44 (four 11-bit coordinates), count 21,
centroid X 11, centroid Y 11, supported-pixel percentage 7, quality 2,
rank/decision 24, valid 1, candidate-bank header 7. Rank's old top 11 zero bits
and the decision's old top four zero bits are removed without losing data.
The two internal history boxes are now 88 bits.

Result low fields keep their previous offsets. Extensions use these former
zero bits; all accessors are defined in the shared header:

| Bit | Extension |
|---|---|
| 224, 225, 226 | A centroid Y, B centroid Y, tip Y bit 10 |
| 227, 228 | A bbox Y0, Y1 bit 10 |
| 229, 230 | B bbox Y0, Y1 bit 10 |
| 248, 249 | A, B region area bit 20 |
| 250, 251 | Raw A, B pixel total bit 20 |
| 252, 253 | Supported A, B pixel total bit 20 |

The complete native frame contains 2,073,600 pixels. Grid statistics remain
80×45 cells; 24×24 cells hold exact counts and local coordinate moments.
Each cell has two 10-bit counts, four 13-bit moments and two 10-bit support
counts, totaling 92 bits. Frame moments remain within 31 unsigned bits.
Global moments use bounded shift/add arithmetic instead of extra DSPs.

Calibration material/white sampling uses a centered 32×32 region and retains
64 four-pixel groups per source frame (16 alternate rows × four groups).
The background uses 48 full-field groups (192 pixels) plus 16 directed groups
(64 pixels) selected inside a centered 16×16 region. Every step still stores
2,048 native pixels from eight complete frames. The native 8×8 mean-intensity
probe is separate. Three-frame confirmation and fifteen-frame identity expiry
keep their existing frame-count semantics.

Run `scripts/test_fhd_processing.py` using the bundled Python executable.
Each run writes an independent timestamped fixture, log, input hashes and
exit status under `build/sim/fhd_processing` and `reports/fhd/processing`.
Historical failures remain available and are not passing evidence.
