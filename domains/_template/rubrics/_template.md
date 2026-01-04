# [Element] Evaluation Rubric

> Systematic framework for evaluating [element] quality.

## Quick Assessment

Before detailed evaluation, check:
- [ ] Does it exist? (If not, score = 0)
- [ ] Is it visible/accessible?
- [ ] Does it match the context/audience?

---

## Evaluation Dimensions

### Dimension 1: [Name] (Weight: X%)

**Definition**: [What this dimension measures]

**Scoring**:

| Score | Criteria |
|-------|----------|
| 10 | Exceptional - [specific criteria that earns a 10] |
| 8 | Good - [specific criteria for 8] |
| 6 | Adequate - [specific criteria for 6] |
| 4 | Below average - [specific criteria for 4] |
| 2 | Poor - [specific criteria for 2] |

**Examples**:
- Score 10: "[Actual example of exceptional work]"
- Score 5: "[Actual example of mediocre work]"
- Score 2: "[Actual example of poor work]"

---

### Dimension 2: [Name] (Weight: X%)

**Definition**: [What this dimension measures]

**Scoring**:

| Score | Criteria |
|-------|----------|
| 10 | [Exceptional criteria] |
| 8 | [Good criteria] |
| 6 | [Adequate criteria] |
| 4 | [Below average criteria] |
| 2 | [Poor criteria] |

**Examples**:
- Score 10: "[Example]"
- Score 5: "[Example]"
- Score 2: "[Example]"

---

### Dimension 3: [Name] (Weight: X%)

**Definition**: [What this dimension measures]

**Scoring**:

| Score | Criteria |
|-------|----------|
| 10 | [Exceptional criteria] |
| 8 | [Good criteria] |
| 6 | [Adequate criteria] |
| 4 | [Below average criteria] |
| 2 | [Poor criteria] |

**Examples**:
- Score 10: "[Example]"
- Score 5: "[Example]"
- Score 2: "[Example]"

---

## Overall Score Calculation

```
Overall = (D1 × W1) + (D2 × W2) + (D3 × W3)
```

Where weights sum to 1.0.

## Automatic Deductions

Issues that reduce the score regardless of other factors:

| Issue | Deduction | Reason |
|-------|-----------|--------|
| [Critical issue 1] | -2 points | [Why this is serious] |
| [Critical issue 2] | -1 point | [Why this matters] |
| [Critical issue 3] | -1 point | [Why this matters] |

## Context Modifiers

Adjust scoring based on context:

| Context | Modifier |
|---------|----------|
| [Context 1, e.g., "B2B audience"] | [How it affects scoring] |
| [Context 2, e.g., "Cold traffic"] | [How it affects scoring] |
| [Context 3, e.g., "Mobile-first"] | [How it affects scoring] |

---

## Output Format

Return evaluation results in this JSON structure:

```json
{
  "element": "[what was evaluated]",
  "overall_score": 0.0,
  "dimensions": [
    {
      "name": "[Dimension 1]",
      "score": 0,
      "weight": 0.0,
      "notes": "[specific observations about this dimension]"
    },
    {
      "name": "[Dimension 2]",
      "score": 0,
      "weight": 0.0,
      "notes": "[specific observations]"
    }
  ],
  "deductions": [
    {
      "issue": "[what was wrong]",
      "points": -1,
      "evidence": "[quote or specific reference]"
    }
  ],
  "strengths": [
    "[Specific strength with evidence]"
  ],
  "weaknesses": [
    "[Specific weakness with evidence]"
  ],
  "recommendations": [
    "[OPTIMIZE] [Actionable recommendation for existing element]",
    "[ADD NEW] [Recommendation for new element]"
  ]
}
```

---

## Evaluation Checklist

Before finalizing the evaluation:

- [ ] Each score is justified with specific evidence
- [ ] Recommendations reference actual content (not fabricated)
- [ ] [OPTIMIZE] recommendations target existing elements
- [ ] [ADD NEW] recommendations are clearly marked
- [ ] Context modifiers have been applied
- [ ] Automatic deductions have been checked
