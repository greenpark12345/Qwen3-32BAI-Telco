#!/usr/bin/env python3
"""
Main Solver Module
Integrates all modules, executes complete problem solving workflow
Focused on Phase 2 processing with 863 questions
"""

import csv
import json
import re
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config_loader import get_config
from .data_parser import (
    get_question_type, extract_options_from_question, 
    extract_option_mapping, extract_features, extract_case_features,
    get_cause_to_option_reverse_map
)
from .rule_engine import (
    solve_standard_question_with_confidence,
    solve_nonstandard_telecom_with_confidence,
    format_answer
)
from .ai_client import process_ai_task
from .case_library import build_case_library, find_similar_cases

# Thread lock
stats_lock = threading.Lock()


class Solver:
    """5G Network Problem Diagnosis Solver"""
    
    def __init__(self):
        self.config = get_config()
        self.output_dir = Path(self.config.get('OUTPUT_DIR', 'output'))
        self.log_file = self.output_dir / "solve_log.jsonl"
        self.progress_file = self.output_dir / "progress.json"
        self.submission_file = self.output_dir / "submission.csv"
        
        self.stats = {
            'standard_high': 0, 'standard_low': 0,
            'nonstandard_telecom_high': 0, 'nonstandard_telecom_low': 0,
            'nonstandard_other': 0,
            'ai_called': 0, 'ai_success': 0, 'ai_failed': 0,
        }
    
    def init_output_dir(self):
        """Initialize output directory"""
        self.output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {self.output_dir.absolute()}")
    
    def log_question(self, log_entry):
        """Log question entry"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def load_progress(self):
        """Load progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'processed_ids': [], 'results': [], 'ai_results': {}}
    
    def save_progress(self, progress):
        """Save progress"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def run(self):
        """Execute solving workflow"""
        self.init_output_dir()
        build_case_library(self.output_dir)
        
        # Load progress
        progress = self.load_progress()
        processed_ids = set(progress.get('processed_ids', []))
        results = progress.get('results', [])
        ai_results_cache = progress.get('ai_results', {})
        
        is_fresh_start = len(processed_ids) == 0 and len(ai_results_cache) == 0
        
        if is_fresh_start:
            if self.log_file.exists():
                self.log_file.unlink()
            print("Fresh start, clearing historical logs")
        else:
            print(f"Checkpoint resume mode: processed {len(processed_ids)} questions, cached AI results {len(ai_results_cache)}")
        
        ai_questions = []
        ai_tasks = []
        
        # ========== Process test data ==========
        test_file = self.config.get('TEST_FILE', 'phase_2_test.csv')
        print(f"\nLoading test data: {test_file}")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            test_rows = list(reader)
        
        print(f"Total {len(test_rows)} questions to process")
        
        phase2_data = {}
        
        for i, row in enumerate(test_rows):
            qid = row['ID']
            if qid in processed_ids:
                continue
            
            question = row['question']
            options = extract_options_from_question(question)
            option_mapping = extract_option_mapping(question)
            question_type = get_question_type(question)
            
            needs_ai = False
            rule_desc = ""
            cause_type = ""
            excluded_opts = []
            remaining_opts = []
            features_dict = {}
            confidence = 'low'
            
            if question_type == 'standard':
                features = extract_features(question)
                features_dict = features or {}
                
                if len(options) != 8:
                    cause_to_option, _ = get_cause_to_option_reverse_map(question)
                    answer, confidence, cause_type, rule_desc = solve_standard_question_with_confidence(
                        features, option_mapping, options)
                    
                    cause_code = None
                    if cause_type == 'weak_coverage': cause_code = 'C1'
                    elif cause_type == 'overshoot': cause_code = 'C2'
                    elif cause_type == 'neighbor_higher': cause_code = 'C3'
                    elif cause_type == 'overlap': cause_code = 'C4'
                    elif cause_type == 'handover': cause_code = 'C5'
                    elif cause_type == 'pci_conflict': cause_code = 'C6'
                    elif cause_type == 'high_speed': cause_code = 'C7'
                    elif cause_type == 'low_rb': cause_code = 'C8'
                    
                    if cause_code and cause_code in cause_to_option:
                        answer = cause_to_option[cause_code]
                    else:
                        available_c1c3 = [c for c in ['C1', 'C3'] if c in cause_to_option]
                        if len(available_c1c3) == 1:
                            answer = cause_to_option[available_c1c3[0]]
                        elif len(available_c1c3) == 2:
                            if cause_type == 'weak_coverage':
                                answer = cause_to_option['C1']
                            else:
                                answer = cause_to_option['C3']
                        else:
                            answer = options[0] if options else '1'
                else:
                    answer, confidence, cause_type, rule_desc = solve_standard_question_with_confidence(
                        features, option_mapping, options)
                
                if confidence == 'high':
                    self.stats['standard_high'] += 1
                else:
                    self.stats['standard_low'] += 1
                
                needs_ai = False
            
            elif question_type == 'nonstandard_telecom':
                answer, confidence, cause_type, excluded_set, nt_features, rule_desc = solve_nonstandard_telecom_with_confidence(
                    question, option_mapping, options)
                
                features_dict = nt_features
                excluded_opts = sorted(excluded_set)
                remaining_opts = sorted(set('ABCDEFGHI') - excluded_set)
                
                if confidence == 'high':
                    self.stats['nonstandard_telecom_high'] += 1
                    needs_ai = False
                else:
                    self.stats['nonstandard_telecom_low'] += 1
                    needs_ai = True
            
            else:
                self.stats['nonstandard_other'] += 1
                answer = options[0] if options else '1'
                needs_ai = True
                rule_desc = "Non-telecom question, needs AI"
                remaining_opts = options
                
                case_features = extract_case_features(question)
                if case_features:
                    similar_cases = find_similar_cases(question, case_features, n=5)
                else:
                    similar_cases = []
                
                features_dict = {'similar_cases_count': len(similar_cases)}
            
            phase2_data[qid] = {
                'question': question,
                'options': options,
                'question_type': question_type,
                'needs_ai': needs_ai,
                'rule_answer': answer,
                'rule_desc': rule_desc,
                'cause_type': cause_type,
                'confidence': confidence if question_type != 'nonstandard_other' else 'none',
                'excluded_opts': excluded_opts,
                'remaining_opts': remaining_opts,
                'features_dict': features_dict,
            }
            
            if needs_ai:
                ai_questions.append({
                    'ID': qid,
                    'type': question_type,
                    'rule_answer': answer,
                })
                
                if qid not in ai_results_cache:
                    task = {
                        'qid': qid,
                        'question': question,
                        'options': remaining_opts if remaining_opts else options,
                        'rule_answer': answer,
                    }
                    ai_tasks.append(task)
            
            if (i + 1) % 100 == 0:
                print(f"  Rule processing progress: {i+1}/{len(test_rows)}")
        
        print(f"\nRule processing completed:")
        print(f"  Standard questions: {self.stats['standard_high'] + self.stats['standard_low']} (high confidence:{self.stats['standard_high']}, low confidence:{self.stats['standard_low']})")
        print(f"  Non-standard telecom: {self.stats['nonstandard_telecom_high'] + self.stats['nonstandard_telecom_low']} (high confidence:{self.stats['nonstandard_telecom_high']}, low confidence:{self.stats['nonstandard_telecom_low']})")
        print(f"  Non-telecom questions: {self.stats['nonstandard_other']}")
        print(f"  Needs AI: {len(ai_questions)} (pending: {len(ai_tasks)}, cached: {len(ai_results_cache)})")
        
        # ========== AI execution ==========
        if ai_tasks:
            max_workers = self.config.get('MAX_WORKERS', 8)
            print(f"\nStarting AI calls ({max_workers} threads)...")
            print(f"Model: {self.config['MODEL']}")
            print("Press Ctrl+C to safely interrupt and save progress")
            
            failed_tasks = []
            interrupted = False
            completed = 0
            
            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_task = {executor.submit(process_ai_task, task): task for task in ai_tasks}
                    
                    for future in as_completed(future_to_task):
                        if interrupted:
                            break
                        task = future_to_task[future]
                        try:
                            result = future.result()
                            qid = result['qid']
                            
                            with stats_lock:
                                self.stats['ai_called'] += 1
                                if result['ai_success']:
                                    self.stats['ai_success'] += 1
                                    ai_results_cache[qid] = {
                                        'answer': result['ai_answer'],
                                        'success': True,
                                    }
                                else:
                                    self.stats['ai_failed'] += 1
                                    failed_tasks.append(task)
                            
                            completed += 1
                            if completed % 10 == 0:
                                print(f"  Progress: {completed}/{len(ai_tasks)}")
                                self.save_progress({
                                    'processed_ids': list(processed_ids),
                                    'results': results,
                                    'ai_results': ai_results_cache,
                                })
                                
                        except Exception as e:
                            print(f"  [{task['qid']}] Exception: {e}")
                            failed_tasks.append(task)
            except KeyboardInterrupt:
                print("\n\nInterrupt signal detected, saving progress...")
                interrupted = True
                self.save_progress({
                    'processed_ids': list(processed_ids),
                    'results': results,
                    'ai_results': ai_results_cache,
                })
                print(f"Saved {len(ai_results_cache)} AI results to cache")
                raise
            
            # Retry logic
            max_retry_rounds = 3
            retry_round = 0
            while failed_tasks and retry_round < max_retry_rounds:
                retry_round += 1
                current_failed = failed_tasks.copy()
                failed_tasks = []
                print(f"\nRetry round {retry_round} ({len(current_failed)} failed tasks)...")
                time.sleep(5)
                with ThreadPoolExecutor(max_workers=max(1, max_workers // 2)) as executor:
                    future_to_task = {executor.submit(process_ai_task, task): task for task in current_failed}
                    for future in as_completed(future_to_task):
                        task = future_to_task[future]
                        try:
                            result = future.result()
                            qid = result['qid']
                            if result['ai_success']:
                                with stats_lock:
                                    self.stats['ai_success'] += 1
                                    self.stats['ai_failed'] -= 1
                                ai_results_cache[qid] = {
                                    'answer': result['ai_answer'],
                                    'success': True,
                                }
                                print(f"  [{qid}] Retry succeeded: {result['ai_answer']}")
                            else:
                                failed_tasks.append(task)
                        except Exception as e:
                            print(f"  [{task['qid']}] Retry exception: {e}")
                            failed_tasks.append(task)
                self.save_progress({
                    'processed_ids': list(processed_ids),
                    'results': results,
                    'ai_results': ai_results_cache,
                })
        
        # ========== Generate results ==========
        print("\nGenerating final results...")
        
        for row in test_rows:
            qid = row['ID']
            if qid in processed_ids:
                continue
            
            data = phase2_data[qid]
            answer = data['rule_answer']
            
            if data['needs_ai'] and qid in ai_results_cache:
                ai_result = ai_results_cache[qid]
                if ai_result.get('success', ai_result.get('ai_success', False)):
                    answer = ai_result.get('answer', ai_result.get('ai_answer', answer))
            
            log_entry = {
                'id': qid,
                'type': data['question_type'],
                'rule': data['rule_desc'],
                'answer': answer,
                'needs_ai': data['needs_ai'],
            }
            self.log_question(log_entry)
            
            formatted = format_answer(answer)
            
            col2_answer = formatted
            col3_answer = 'placeholder'
            col4_answer = 'placeholder'
            
            for suffix in ['_1', '_2', '_3', '_4']:
                results.append({
                    'ID': qid + suffix,
                    'combined': col2_answer,
                    'rule_based': col3_answer,
                    'ai_based': col4_answer,
                })
            
            processed_ids.add(qid)
        
        self.save_progress({
            'processed_ids': list(processed_ids),
            'results': results,
            'ai_results': ai_results_cache,
        })
        
        # Statistics
        total_questions = (self.stats['standard_high'] + self.stats['standard_low'] +
                         self.stats['nonstandard_telecom_high'] + self.stats['nonstandard_telecom_low'] +
                         self.stats['nonstandard_other'])
        
        print(f"\n========== Statistics ==========")
        print(f"Total questions: {total_questions}")
        print(f"  Standard questions: {self.stats['standard_high'] + self.stats['standard_low']}")
        print(f"  Non-standard telecom: {self.stats['nonstandard_telecom_high'] + self.stats['nonstandard_telecom_low']}")
        print(f"  Non-telecom questions: {self.stats['nonstandard_other']}")
        
        if self.stats['ai_called'] > 0:
            print(f"\nAI Calls:")
            print(f"  Total calls: {self.stats['ai_called']}")
            print(f"  Successful: {self.stats['ai_success']}")
            print(f"  Failed: {self.stats['ai_failed']}")
        
        # Generate submission file
        with open(self.submission_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['ID', 'Qwen3-32B', 'Qwen2.5-7B-Instruct', 'Qwen2.5-1.5B-Instruct']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    'ID': r['ID'],
                    'Qwen3-32B': r['combined'],
                    'Qwen2.5-7B-Instruct': r['rule_based'],
                    'Qwen2.5-1.5B-Instruct': r['ai_based'],
                })
        
        print(f"\nGenerated submission file: {self.submission_file}")
        print(f"Total {len(results)} rows ({len(results)//4} questions x 4 sub-questions)")


def main():
    """Main entry function"""
    solver = Solver()
    solver.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupt signal detected...")
        print("Progress saved")
    except Exception as e:
        print(f"\nProgram exception: {e}")
        import traceback
        traceback.print_exc()
