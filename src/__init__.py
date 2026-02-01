"""
5G Network Problem Diagnosis Solver
Module Package Initialization File
"""

__version__ = "1.0.0"
__author__ = "5G Solver Team"

from .solver import Solver, main
from .config_loader import load_config, get_config
from .data_parser import (
    get_question_type,
    extract_options_from_question,
    extract_option_mapping,
    extract_features,
    extract_case_features,
)
from .rule_engine import (
    solve_standard_question_with_confidence,
    solve_nonstandard_telecom_with_confidence,
    format_answer,
)
from .ai_client import (
    call_ai_api,
    extract_ai_answer,
    process_ai_task,
)
from .case_library import (
    build_case_library,
    find_similar_cases,
    compute_similarity,
)

__all__ = [
    'Solver',
    'main',
    'load_config',
    'get_config',
    'get_question_type',
    'extract_options_from_question',
    'extract_option_mapping',
    'extract_features',
    'extract_case_features',
    'solve_standard_question_with_confidence',
    'solve_nonstandard_telecom_with_confidence',
    'format_answer',
    'call_ai_api',
    'extract_ai_answer',
    'process_ai_task',
    'build_case_library',
    'find_similar_cases',
    'compute_similarity',
]
