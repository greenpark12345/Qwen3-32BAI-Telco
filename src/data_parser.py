#!/usr/bin/env python3
"""
Data Parser Module
Responsible for parsing question data, extracting features, and parsing options
"""

import re


def is_standard_question(question):
    """Check if question is a standard question"""
    return 'Timestamp|Longitude|Latitude|GPS Speed' in question


def is_nonstandard_telecom_question(question):
    """Check if question is a non-standard telecom question"""
    has_telecom_data = ('Drive Test Data' in question or 
                        'Serving RSRP' in question or 
                        'Throughput' in question or
                        'Parameter Data' in question)
    is_standard = is_standard_question(question)
    return has_telecom_data and not is_standard


def get_question_type(question):
    """Get question type"""
    if is_standard_question(question):
        return 'standard'
    elif is_nonstandard_telecom_question(question):
        return 'nonstandard_telecom'
    else:
        return 'nonstandard_other'


def extract_options_from_question(question):
    """Extract options from question"""
    options = []
    lines = question.split('\n')
    
    # Options with prefix (e.g., A1, B2)
    prefix_options = []
    for line in lines:
        line = line.strip()
        match = re.match(r'^([A-Z])(\d+)\s*:', line)
        if match:
            prefix_options.append(f"{match.group(1)}{match.group(2)}")
    
    if prefix_options:
        seen = set()
        for opt in prefix_options:
            if opt not in seen:
                seen.add(opt)
                options.append(opt)
        return options
    
    # Numeric options
    num_options = []
    for line in lines:
        line = line.strip()
        match = re.match(r'^(\d+)\s*:', line)
        if match:
            num_options.append(match.group(1))
    
    if num_options:
        seen = set()
        for m in num_options:
            if m not in seen:
                seen.add(m)
                options.append(m)
        return options
    
    # Letter options
    letter_options = []
    for line in lines:
        line = line.strip()
        match = re.match(r'^([A-I])\s*:', line)
        if match:
            letter_options.append(match.group(1))
    
    if letter_options:
        return sorted(set(letter_options))
    
    return ['1', '2', '3', '4', '5', '6', '7', '8']


def extract_option_mapping(question):
    """Extract option to root cause type mapping"""
    from .prompts import ROOT_CAUSE_KEYWORDS, NONSTANDARD_KEYWORDS
    
    mapping = {}
    lines = question.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.match(r'^([A-Z]?\d+|[A-I])\s*:\s*(.+)$', line)
        if match:
            option_id = match.group(1)
            description = match.group(2).lower()
            
            for cause_type, keywords in ROOT_CAUSE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in description:
                        mapping[cause_type] = option_id
                        break
            
            for cause_type, keywords in NONSTANDARD_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in description:
                        mapping[cause_type] = option_id
                        break
    
    return mapping


def get_cause_to_option_reverse_map(question):
    """Get cause code (C1-C8) to option mapping"""
    CAUSE_KEYWORDS = {
        'C1': ['downtilt', 'weak coverage', 'far end'],
        'C2': ['coverage distance exceeds', 'over-shooting', 'overshooting'],
        'C3': ['neighboring cell provides higher'],
        'C4': ['overlapping coverage', 'overlapping'],
        'C5': ['frequent handover', 'handovers degrade'],
        'C6': ['PCI mod 30'],
        'C7': ['speed exceeds 40'],
        'C8': ['RBs are below', 'scheduled RBs']
    }
    
    cause_to_option = {}
    option_to_cause = {}
    
    lines = question.split('\n')
    for line in lines:
        line = line.strip()
        match = re.match(r'^([A-Z]?\d+|[A-I])\s*:\s*(.+)$', line)
        if match:
            option_id = match.group(1)
            description = match.group(2).lower()
            
            for cause, keywords in CAUSE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in description:
                        cause_to_option[cause] = option_id
                        option_to_cause[option_id] = cause
                        break
    
    return cause_to_option, option_to_cause


def parse_drive_test_data(question):
    """Parse drive test data"""
    lines = question.split('\n')
    drive_test_header = None
    drive_test_start = -1
    eng_header = None
    eng_start = -1
    
    for i, line in enumerate(lines):
        if 'Timestamp|Longitude|Latitude|GPS Speed' in line:
            drive_test_header = line
            drive_test_start = i + 1
        elif 'gNodeB ID|Cell ID|Longitude|Latitude' in line:
            eng_header = line
            eng_start = i + 1
    
    drive_test_records = []
    if drive_test_header and drive_test_start > 0:
        headers = [h.strip() for h in drive_test_header.split('|')]
        for line in lines[drive_test_start:]:
            if '|' not in line or line.strip().startswith('gNodeB') or 'Engineering' in line:
                break
            parts = line.split('|')
            if len(parts) == len(headers):
                drive_test_records.append(dict(zip(headers, [p.strip() for p in parts])))
    
    eng_records = []
    if eng_header and eng_start > 0:
        headers = [h.strip() for h in eng_header.split('|')]
        for line in lines[eng_start:]:
            if '|' not in line:
                break
            parts = line.split('|')
            if len(parts) == len(headers):
                eng_records.append(dict(zip(headers, [p.strip() for p in parts])))
    
    return drive_test_records, eng_records


def extract_features(question):
    """Extract question features for rule-based judgment"""
    dt_records, eng_records = parse_drive_test_data(question)
    
    if not dt_records:
        return None
    
    pci_to_eng = {}
    for eng in eng_records:
        try:
            pci = int(eng.get('PCI', -1))
            pci_to_eng[pci] = eng
        except:
            pass
    
    speeds = []
    serving_pcis = []
    neighbor_top1_pcis = set()
    rbs = []
    rsrps = []
    prev_serving_pci = None
    handovers = 0
    
    for r in dt_records:
        try:
            speeds.append(float(r.get('GPS Speed (km/h)', 0)))
        except:
            pass
        
        try:
            pci = int(r.get('5G KPI PCell RF Serving PCI', -1))
            serving_pcis.append(pci)
            if prev_serving_pci is not None and prev_serving_pci != pci:
                handovers += 1
            prev_serving_pci = pci
        except:
            pass
        
        try:
            n1_pci = r.get('Measurement PCell Neighbor Cell Top Set(Cell Level) Top 1 PCI', '-')
            if n1_pci and n1_pci != '-':
                neighbor_top1_pcis.add(int(n1_pci))
        except:
            pass
        
        try:
            rbs.append(float(r.get('5G KPI PCell Layer1 DL RB Num (Including 0)', 200)))
        except:
            pass
        
        try:
            rsrps.append(float(r.get('5G KPI PCell RF Serving SS-RSRP [dBm]', -80)))
        except:
            pass
    
    tilts = []
    for pci in set(serving_pcis):
        if pci in pci_to_eng:
            eng = pci_to_eng[pci]
            try:
                md = float(eng.get('Mechanical Downtilt', 0))
                dt = eng.get('Digital Tilt', 0)
                if dt == '255' or dt == 255:
                    dt = 6
                else:
                    dt = float(dt)
                tilts.append(md + dt)
            except:
                pass
    
    has_pci_conflict = False
    mod30_values = []
    for pci in set(serving_pcis) | neighbor_top1_pcis:
        mod30_values.append(pci % 30)
    if len(mod30_values) != len(set(mod30_values)):
        has_pci_conflict = True
    
    return {
        'min_rsrp': min(rsrps) if rsrps else -999,
        'avg_rsrp': sum(rsrps)/len(rsrps) if rsrps else -999,
        'max_tilt': max(tilts) if tilts else 0,
        'min_tilt': min(tilts) if tilts else 999,
        'total_tilt': sum(tilts),
        'handovers': handovers,
        'num_neighbors': len(neighbor_top1_pcis),
        'max_speed': max(speeds) if speeds else 0,
        'avg_rb': sum(rbs)/len(rbs) if rbs else 999,
        'has_pci_conflict': has_pci_conflict
    }


def extract_case_features(question):
    """Extract case features (for similarity calculation)"""
    features = {
        'min_rsrp': None,
        'max_tilt': None,
        'total_tilt': None,
        'handovers': None,
        'max_speed': None,
        'avg_rb': None,
        'num_neighbors': None,
    }
    
    # Find header
    lines = question.split('\n')
    headers = None
    header_idx = -1
    
    for i, line in enumerate(lines):
        if 'Timestamp|Longitude|Latitude|GPS Speed' in line:
            headers = [h.strip() for h in line.split('|')]
            header_idx = i
            break
    
    if not headers:
        return features
    
    # Find column indices
    def find_col(names):
        for name in names:
            for j, h in enumerate(headers):
                if name in h:
                    return j
        return -1
    
    rsrp_col = find_col(['Serving SS-RSRP', 'Serving RSRP'])
    speed_col = find_col(['GPS Speed'])
    pci_col = find_col(['Serving PCI'])
    n1_pci_col = find_col(['Top 1 PCI'])
    rb_col = find_col(['DL RB Num'])
    
    # Parse data rows
    rsrps = []
    speeds = []
    pcis = []
    n1_pcis = set()
    rbs = []
    
    for line in lines[header_idx + 1:]:
        if '|' not in line or 'gNodeB' in line or 'Engineering' in line:
            break
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < len(headers):
            continue
        
        try:
            if rsrp_col >= 0 and parts[rsrp_col] and parts[rsrp_col] != '-':
                rsrps.append(float(parts[rsrp_col]))
        except:
            pass
        
        try:
            if speed_col >= 0 and parts[speed_col] and parts[speed_col] != '-':
                speeds.append(float(parts[speed_col]))
        except:
            pass
        
        try:
            if pci_col >= 0 and parts[pci_col] and parts[pci_col] != '-':
                pcis.append(int(parts[pci_col]))
        except:
            pass
        
        try:
            if n1_pci_col >= 0 and parts[n1_pci_col] and parts[n1_pci_col] != '-':
                n1_pcis.add(int(parts[n1_pci_col]))
        except:
            pass
        
        try:
            if rb_col >= 0 and parts[rb_col] and parts[rb_col] != '-':
                rbs.append(float(parts[rb_col]))
        except:
            pass
    
    # Calculate handover count
    handovers = 0
    for i in range(1, len(pcis)):
        if pcis[i] != pcis[i-1]:
            handovers += 1
    
    # Extract tilt angles from engineering parameters
    tilts = []
    for line in lines:
        if 'gNodeB ID|Cell ID|Longitude|Latitude' in line:
            eng_headers = [h.strip() for h in line.split('|')]
            eng_idx = lines.index(line)
            
            md_col = -1
            dt_col = -1
            for j, h in enumerate(eng_headers):
                if 'Mechanical Downtilt' in h:
                    md_col = j
                if 'Digital Tilt' in h:
                    dt_col = j
            
            for eng_line in lines[eng_idx + 1:]:
                if '|' not in eng_line:
                    break
                eng_parts = [p.strip() for p in eng_line.split('|')]
                if len(eng_parts) < len(eng_headers):
                    continue
                
                try:
                    md = float(eng_parts[md_col]) if md_col >= 0 and eng_parts[md_col] else 0
                    dt_val = eng_parts[dt_col] if dt_col >= 0 else '0'
                    if dt_val == '255':
                        dt = 6
                    else:
                        dt = float(dt_val) if dt_val else 0
                    tilts.append(md + dt)
                except:
                    pass
            break
    
    if rsrps:
        features['min_rsrp'] = min(rsrps)
    if tilts:
        features['max_tilt'] = max(tilts)
        features['total_tilt'] = sum(tilts)
    if handovers >= 0:
        features['handovers'] = handovers
    if speeds:
        features['max_speed'] = max(speeds)
    if rbs:
        features['avg_rb'] = sum(rbs) / len(rbs)
    features['num_neighbors'] = len(n1_pcis)
    
    return features
