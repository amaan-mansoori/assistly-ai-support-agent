# Human Audit — 8-Annotator Analysis

## What was analyzed

- 50 shared audit cases
- 8 independent human annotators = 400 decisions per binary/categorical dimension
- A calibrated reference panel uses 5 annotators with case-specific variation: Adnan, Jatin, Khushi, Rashi, Yash.
- Kuhu, Sabir, and Shivani are retained in the raw data but flagged for near-constant response patterns on at least one dimension; their labels are not silently deleted or corrected.
- The previous three-AI judge comparison is treated as a pre-existing judge analysis, not as human ground truth.

## Human agreement

| Dimension | 8-human mean top-label agreement | 5-human panel mean top-label agreement |
|---|---:|---:|
| Reply addresses problem | 64.0% | 78.8% |
| Evidence supported | 55.0% | 61.6% |
| Unsupported claim | 65.8% | 84.0% |
| Human escalation | 61.8% | 67.6% |

## Copilot vs calibrated human panel

| Dimension | Exact agreement |
|---|---:|
| Reply addresses problem | 72.0% |
| Evidence supported | 52.0% |
| Unsupported claim | 94.0% |
| Human escalation | 68.0% |

### Interpretation

The strongest signal is that Copilot is much more lenient on evidence support and unsupported-claim detection than the calibrated human panel. Its unsupported-claim exact agreement is high because most cases are genuinely `no`, but it still misses the minority cases where humans identify unsupported claims.

The evidence-support dimension has materially lower agreement, which confirms that evidence sufficiency is the hardest rubric dimension and should not be presented as an objective binary truth.

## AI judge Q1 coverage

The previous three-judge comparison did not provide complete structured Q1 labels for all three judges. Therefore the table below is **coverage-limited** and is not a full judge leaderboard.

- **Copilot**: 50/50 comparable cases; exact agreement = 64.0%
- **ChatGPT**: 12/50 comparable cases; exact agreement = 75.0%
- **Gemini**: 3/50 comparable cases; exact agreement = 66.7%

## Important methodological decision

Do **not** retroactively modify the human rubric or the generated replies based on the three AI judges. The human annotations are now the independent external audit. Any AI-identified cases such as `golden-set-0013`, `0013`, `0175`, or `0054` should be treated as hypotheses/checkpoints, not pre-declared truth.

## Next implementation step

1. Preserve all eight raw exports.
2. Add the calibrated human-panel analysis to the evaluation report.
3. Keep the existing real Gemini LLM-judge results (220 cases) as the automated judge result.
4. Use the 50-case human audit to report judge agreement/limitations, not as a replacement for the 220-case automated evaluation.
5. Add a concise failure-analysis section using cases where the human panel is reasonably strong and the judge/model disagrees.
