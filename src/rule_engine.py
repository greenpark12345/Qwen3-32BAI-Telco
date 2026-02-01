#!/usr/bin/env python3
"""
Rule Engine Module
Rule-based problem solving logic
"""


def solve_standard_question_with_confidence(features, option_mapping, default_options):
    """
    Rule-based solver for standard questions
    
    Args:
        features: Extracted question features
        option_mapping: Option to root cause type mapping
        default_options: Default option list
        
    Returns:
        tuple: (answer, confidence, cause_type, rule_desc)
    """
    cause_type = 'neighbor_higher'
    confidence = 'low'
    rule_desc = "Default C3"
    
    if features:
        num_neighbors = features.get('num_neighbors', 0)
        handovers = features.get('handovers', 0)
        max_speed = features.get('max_speed', 0)
        avg_rb = features.get('avg_rb', 200)
        min_rsrp = features.get('min_rsrp', -80)
        max_tilt = features.get('max_tilt', 0)
        min_tilt = features.get('min_tilt', 0)
        total_tilt = features.get('total_tilt', 0)
        has_pci_conflict = features.get('has_pci_conflict', False)
        
        # High confidence rules
        if num_neighbors >= 3:
            cause_type = 'overlap'
            confidence = 'high'
            rule_desc = f"Rule 1: num_neighbors={num_neighbors}>=3 => C4(Overlap Coverage)"
        elif handovers >= 3:
            cause_type = 'handover'
            confidence = 'high'
            rule_desc = f"Rule 2: handovers={handovers}>=3 => C5(Frequent Handover)"
        elif handovers == 2:
            cause_type = 'overshoot'
            confidence = 'high'
            rule_desc = f"Rule 3: handovers={handovers}==2 => C2(Overshooting)"
        elif max_speed > 40:
            cause_type = 'high_speed'
            confidence = 'high'
            rule_desc = f"Rule 4: max_speed={max_speed:.1f}>40 => C7(High Speed)"
        elif avg_rb < 170:
            cause_type = 'low_rb'
            confidence = 'high'
            rule_desc = f"Rule 5: avg_rb={avg_rb:.1f}<170 => C8(Low RB)"
        elif has_pci_conflict:
            cause_type = 'pci_conflict'
            confidence = 'high'
            rule_desc = f"Rule 6: PCI mod 30 conflict => C6"
        
        # C3 high confidence
        elif max_tilt < 12:
            cause_type = 'neighbor_higher'
            confidence = 'high'
            rule_desc = f"Rule 7: max_tilt={max_tilt:.1f}<12 => C3(Neighbor Better)"
        elif total_tilt < 19:
            cause_type = 'neighbor_higher'
            confidence = 'high'
            rule_desc = f"Rule 8: total_tilt={total_tilt:.1f}<19 => C3(Neighbor Better)"
        elif min_tilt < 6:
            cause_type = 'neighbor_higher'
            confidence = 'high'
            rule_desc = f"Rule 9: min_tilt={min_tilt:.1f}<6 => C3(Neighbor Better)"
        elif min_tilt < 10 and min_rsrp > -89:
            cause_type = 'neighbor_higher'
            confidence = 'high'
            rule_desc = f"Rule 10: min_tilt={min_tilt:.1f}<10 AND min_rsrp={min_rsrp:.1f}>-89 => C3"
        
        # C1 high confidence
        elif min_rsrp < -90:
            cause_type = 'weak_coverage'
            confidence = 'high'
            rule_desc = f"Rule 11: min_rsrp={min_rsrp:.1f}<-90 => C1(Weak Coverage)"
        elif max_tilt > 29:
            cause_type = 'weak_coverage'
            confidence = 'high'
            rule_desc = f"Rule 12: max_tilt={max_tilt:.1f}>29 => C1(Weak Coverage)"
        elif total_tilt > 52:
            cause_type = 'weak_coverage'
            confidence = 'high'
            rule_desc = f"Rule 13: total_tilt={total_tilt:.1f}>52 => C1(Weak Coverage)"
        elif min_tilt > 25:
            cause_type = 'weak_coverage'
            confidence = 'high'
            rule_desc = f"Rule 14: min_tilt={min_tilt:.1f}>25 => C1(Weak Coverage)"
        
        # Low confidence rules
        elif min_rsrp < -88.5 and total_tilt > 39 and max_tilt >= 22:
            cause_type = 'weak_coverage'
            confidence = 'low'
            rule_desc = f"Rule 15: C1/C3 Boundary (Lean C1)"
        elif min_tilt < 10 or total_tilt <= 35:
            cause_type = 'neighbor_higher'
            confidence = 'low'
            rule_desc = f"Rule 16: C1/C3 Boundary (Lean C3)"
        else:
            cause_type = 'neighbor_higher'
            confidence = 'low'
            rule_desc = f"Rule 17: C1/C3 Boundary (Default C3)"
    
    # Get answer
    answer = None
    if cause_type in option_mapping:
        answer = option_mapping[cause_type]
    else:
        backup_mappings = {
            'neighbor_higher': ['overlap', 'neighbor_higher'],
            'overlap': ['neighbor_higher', 'overlap'],
        }
        if cause_type in backup_mappings:
            for backup in backup_mappings[cause_type]:
                if backup in option_mapping:
                    answer = option_mapping[backup]
                    break
        
        if not answer and default_options:
            idx = min(2, len(default_options) - 1)
            answer = default_options[idx]
        elif not answer:
            answer = '3'
    
    return answer, confidence, cause_type, rule_desc


def solve_nonstandard_telecom_with_confidence(question, option_mapping, default_options):
    """
    Rule-based solver for non-standard telecom questions
    Uses elimination method to determine answer
    
    Args:
        question: Question text
        option_mapping: Option to root cause type mapping
        default_options: Default option list
        
    Returns:
        tuple: (answer, confidence, cause_type, excluded_options, features, rule_desc)
    """
    lines = question.split('\n')
    data_rows = []
    header = None
    
    for line in lines:
        if '|' in line and not line.strip().startswith('|:'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if header is None and len(parts) > 3:
                if 'Time' in line or 'Timestamp' in line or 'UE' in line:
                    header = parts
            elif header and len(parts) >= len(header) - 2:
                data_rows.append(dict(zip(header, parts)))
    
    rsrps = []
    sinrs = []
    cces = []
    handovers = 0
    prev_pci = None
    
    for r in data_rows:
        try:
            for col in ['Serving RSRP(dBm)', 'RSRP', 'Serving RSRP']:
                if col in r:
                    rsrps.append(float(r[col]))
                    break
        except:
            pass
        
        try:
            for col in ['Serving SINR(dB)', 'SINR', 'Serving SINR']:
                if col in r:
                    sinrs.append(float(r[col]))
                    break
        except:
            pass
        
        try:
            for col in ['CCE Fail Rate', 'CCE']:
                if col in r:
                    cces.append(float(r[col]))
                    break
        except:
            pass
        
        try:
            for col in ['Serving PCI', 'PCI']:
                if col in r:
                    pci = int(r[col])
                    if prev_pci is not None and prev_pci != pci:
                        handovers += 1
                    prev_pci = pci
                    break
        except:
            pass
    
    min_rsrp = min(rsrps) if rsrps else -100
    mean_sinr = sum(sinrs)/len(sinrs) if sinrs else 0
    max_cce = max(cces) if cces else 0
    
    features = {
        'min_rsrp': min_rsrp,
        'mean_sinr': mean_sinr,
        'max_cce': max_cce,
        'handovers': handovers,
    }
    
    cause_type = None
    confidence = 'low'
    excluded_options = set()
    rule_desc = ""
    
    # High confidence rules
    if min_rsrp < -100:
        cause_type = 'weak_coverage_rf'
        confidence = 'high'
        rule_desc = f"Rule 1: min_rsrp={min_rsrp:.1f}<-100 => Weak Coverage"
    elif handovers >= 3:
        cause_type = 'threshold_low'
        confidence = 'high'
        rule_desc = f"Rule 2: handovers={handovers}>=3 => Threshold Too Low"
    elif max_cce > 0.4:
        cause_type = 'pdcch'
        confidence = 'high'
        rule_desc = f"Rule 3: max_cce={max_cce:.2f}>0.4 => PDCCH Congestion"
    
    # Low confidence elimination method
    if confidence != 'high':
        excluded_rules = []
        excluded_causes = set()
        
        # Exclude causes already determined with high confidence
        excluded_causes.add('weak_coverage_rf')
        excluded_causes.add('threshold_low')
        excluded_causes.add('pdcch')
        excluded_rules.append("Exclude: Weak Coverage, Threshold Too Low, PDCCH")
        
        # Dynamic exclusion rules
        if handovers > 0:
            excluded_causes.add('neighbor_missing')
            excluded_rules.append(f"ho={handovers}>0 Exclude Neighbor Missing")
        
        if mean_sinr > 12:
            excluded_causes.add('overlap')
            excluded_causes.add('overlap_rf')
            excluded_rules.append(f"sinr={mean_sinr:.1f}>12 Exclude Overlap")
        
        if mean_sinr > 8:
            excluded_causes.add('transport_anomaly')
            excluded_causes.add('uplink_issue')
            excluded_rules.append(f"sinr={mean_sinr:.1f}>8 Exclude Transport Anomaly")
        
        # Convert root cause types to option letters
        for cause in excluded_causes:
            if cause in option_mapping:
                excluded_options.add(option_mapping[cause])
        
        cause_type = 'weak_coverage_rf'
        rule_desc = f"Low Confidence: {', '.join(excluded_rules)}"
    
    # Get answer
    answer = None
    if cause_type in option_mapping:
        answer = option_mapping[cause_type]
    else:
        if 'weak_coverage_rf' in option_mapping:
            answer = option_mapping['weak_coverage_rf']
        elif default_options:
            idx = min(5, len(default_options) - 1)
            answer = default_options[idx]
        else:
            answer = 'F'
    
    return answer, confidence, cause_type, excluded_options, features, rule_desc


def format_answer(answer):
    """Format answer output"""
    return f"Based on the provided data, the most likely root cause for throughput drop is: \\boxed{{{answer}}}"
