#!/usr/bin/env python3
"""
AI Prompt Templates
Contains system prompts for 5G network fault diagnosis
"""

# Non-standard telecom question system prompt
NONSTANDARD_TELECOM_SYSTEM = """You are an expert in 5G network fault diagnosis.
The user provides a problem description (Drive Test Data, Engineering Parameters) and a filtered list of Options.
Note: The Options have been filtered by rules, so the correct answer is definitely in the list.

# Analysis Steps
1. **Phenomenon Check**: Identify when throughput drops. Check if SINR becomes negative (heavy interference) or RSRP drops (weak coverage).
2. **Neighbor Comparison**: Compare Serving Cell RSRP vs. Neighbor Cell RSRP.
   - **Overlap**: Multiple neighbors have similar strength to servicing cell (Difference < 3dB).
   - **Strong Neighbor**: One neighbor is significantly stronger (> 5dB) than serving cell.
3. **Handover & Parameter Check**:
   - Check `NREventA3MeasConfig`. A typical `a3-Offset` is 2-3dB.
   - **Threshold Too High**: If `a3-Offset` is high (e.g., >=5dB) AND Neighbor is stronger than Serving cell for a duration before handover (or no handover), it causes interference ("Delayed Handover").
   - **Missing Neighbor**: Strong neighbor exists but no handover occurs (PCI doesn't change).
   - **Overshooting**: Serving cell is far away (check distance) but has strong signal and poor SINR.
4. **Transport/Core**: If RSRP and SINR are good but throughput is low, it's likely a transmission/server issue.

# Output Format
1. **Analysis**: Briefly describe the data patterns (e.g., "At 23:13, SINR drops to -3dB. Neighbor PCI 310 is 6dB stronger than Serving PCI 195. A3 Offset is 5dB (High). Handover is delayed.").
2. **Answer**: Output the final option letter in \\boxed{}.

Example Output:
Analysis: ...
Answer: \\boxed{A}
"""

# Non-telecom question system prompt
NON_TELECOM_SYSTEM = """You are a network technology expert.
Analyze the question and filtered options to find the root cause or correct definition.

# Output Format
Analysis: <Brief reasoning>
Answer: \\boxed{Option Letter}
"""

# Root cause type keyword mapping
ROOT_CAUSE_KEYWORDS = {
    'neighbor_higher': ['neighboring cell provides higher throughput', 'neighbor cell provides higher'],
    'overshoot': ['coverage distance exceeds 1km', 'over-shooting', 'overshooting'],
    'overlap': ['overlapping coverage', 'severe overlapping'],
    'pci_conflict': ['PCI mod 30', 'same PCI mod'],
    'low_rb': ['RBs are below 160', 'scheduled RBs are below', 'Average scheduled RBs'],
    'weak_coverage': ['downtilt angle is too large', 'weak coverage at the far end'],
    'high_speed': ['speed exceeds 40km/h', 'Test vehicle speed exceeds'],
    'handover': ['Frequent handovers', 'handovers degrade'],
}

# Non-standard question keyword mapping
NONSTANDARD_KEYWORDS = {
    'overlap': ['severe overlap', 'overlapping coverage', 'RF or power parameters cause severe overlap'],
    'overlap_rf': ['severe overlapping coverage', 'RF or power parameters cause severe overlapping'],
    'inter_freq_threshold': ['inter-frequency handover threshold', 'Inter-frequency handover'],
    'capacity': ['capacity', 'load imbalance', 'network capacity'],
    'transport_anomaly': ['transport anomaly', 'transmission abnormality', 'upstream traffic', 'Test server or transport'],
    'uplink_issue': ['uplink traffic', 'transmission abnormality'],
    'neighbor_missing': ['neighbor configuration missing', 'Missing neighbor', 'neighbor cell configuration'],
    'weak_coverage_rf': ['weak coverage', 'RF, power parameters or site construction lead to weak coverage', 'site construction cause weak'],
    'threshold_high': ['intra-frequency handover threshold is too high', 'threshold too high', 'handover threshold too high'],
    'threshold_low': ['intra-frequency handover threshold is too low', 'threshold too low', 'frequent handover', 'handover threshold too low'],
    'pdcch': ['PDCCH resource management parameters unreasonable', 'PDCCH', 'resource management', 'CCE'],
}
