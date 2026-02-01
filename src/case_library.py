#!/usr/bin/env python3
"""
Case Library Module (Optional)
Manages historical cases, supports similar case lookup
If no training data exists, this module's functionality will be skipped
"""

import csv
import json
from pathlib import Path

from .config_loader import get_config
from .data_parser import extract_case_features

# Global case library
CASE_LIBRARY = {}


def get_case_library():
    """Get case library singleton"""
    return CASE_LIBRARY


def build_case_library(output_dir):
    """
    Build case library (optional feature)
    If no training data file exists, skip this step
    
    Args:
        output_dir: Output directory Path object
    """
    global CASE_LIBRARY
    config = get_config()
    
    cache_file = output_dir / "case_cache.json"
    
    # Check cache
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                CASE_LIBRARY = json.load(f)
                if CASE_LIBRARY:
                    print(f"Loaded case library from cache: {len(CASE_LIBRARY)} cases")
                return
        except:
            pass
    
    # Check if training data file exists
    train_file = config.get('TRAIN_FILE', '')
    case_file = config.get('CASE_FILE', '')
    
    if not train_file and not case_file:
        print("No training data configured, skipping case library...")
        return
    
    print("Building case library...")
    
    # 1. Load train.csv (if exists)
    if train_file and Path(train_file).exists():
        try:
            with open(train_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    case_id = row['ID']
                    question = row['question']
                    answer = row['answer']
                    
                    features = extract_case_features(question)
                    
                    CASE_LIBRARY[case_id] = {
                        'question_preview': question[:500],
                        'answer': answer,
                        'features': features,
                        'source': 'train',
                    }
            
            print(f"  Loaded from {train_file}: {len(CASE_LIBRARY)} cases")
        except Exception as e:
            print(f"  Warning: Failed to load {train_file}: {e}")
    
    # 2. Load custom case file (if exists)
    if case_file and Path(case_file).exists():
        try:
            with open(case_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    case_id = row.get('ID', f"case_{count}")
                    question = row.get('question', '')
                    answer = row.get('answer', '')
                    
                    if question and answer:
                        features = extract_case_features(question)
                        CASE_LIBRARY[case_id] = {
                            'question_preview': question[:500],
                            'answer': answer,
                            'features': features,
                            'source': 'case_file',
                        }
                        count += 1
            
            print(f"  Loaded from {case_file}: {count} cases")
        except Exception as e:
            print(f"  Warning: Failed to load {case_file}: {e}")
    
    if CASE_LIBRARY:
        print(f"  Total case library: {len(CASE_LIBRARY)} cases")
        # Save cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(CASE_LIBRARY, f, ensure_ascii=False)
    else:
        print("  No cases loaded, case matching disabled")


def compute_similarity(features1, features2):
    """
    Compute similarity between two cases
    
    Args:
        features1: Feature dictionary 1
        features2: Feature dictionary 2
        
    Returns:
        float: Similarity score (0-1)
    """
    if not features1 or not features2:
        return 0.0
    
    weights = {
        'min_rsrp': 2.0,
        'max_tilt': 2.0,
        'total_tilt': 1.5,
        'handovers': 1.5,
        'max_speed': 1.0,
        'avg_rb': 1.0,
        'num_neighbors': 1.0,
    }
    
    normalizers = {
        'min_rsrp': 30.0,
        'max_tilt': 20.0,
        'total_tilt': 50.0,
        'handovers': 5.0,
        'max_speed': 50.0,
        'avg_rb': 100.0,
        'num_neighbors': 5.0,
    }
    
    total_weight = 0
    similarity = 0
    
    for key, weight in weights.items():
        v1 = features1.get(key)
        v2 = features2.get(key)
        
        if v1 is not None and v2 is not None:
            diff = abs(v1 - v2) / normalizers.get(key, 1.0)
            sim = max(0, 1 - diff)
            similarity += weight * sim
            total_weight += weight
    
    return similarity / total_weight if total_weight > 0 else 0.0


def find_similar_cases(question, features, n=5):
    """
    Find top n most similar cases
    
    Args:
        question: Question text
        features: Question features
        n: Number of cases to return
        
    Returns:
        list: List of similar cases (empty list if case library is empty)
    """
    if not features or not CASE_LIBRARY:
        return []
    
    similarities = []
    for case_id, case_data in CASE_LIBRARY.items():
        case_features = case_data.get('features', {})
        sim = compute_similarity(features, case_features)
        similarities.append((case_id, sim, case_data))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return diverse cases (covering different answers)
    result = []
    seen_answers = set()
    
    for case_id, sim, case_data in similarities:
        if len(result) >= n:
            break
        answer = case_data.get('answer', '')
        if answer not in seen_answers or len(result) < 3:
            result.append({
                'id': case_id,
                'similarity': sim,
                'answer': answer,
                'features': case_data.get('features', {}),
                'source': case_data.get('source', 'unknown'),
            })
            seen_answers.add(answer)
    
    return result
