# Research Report: Hybrid Neuro-Symbolic Approach for 5G Fault Diagnosis (Qwen3-32B)

## 1. Executive Summary
This report outlines the development of our solution for the 5G Network Fault Diagnosis challenge. Our team adopted a multi-faceted approach, exploring techniques such as Quantization, Retrieval-Augmented Generation (RAG), K-Nearest Neighbors (KNN), and Rule-Based Engines. 

Our final submission utilizes a hybrid architecture that integrates deterministic telecom domain principles with the semantic reasoning capabilities of the Qwen3-32B model. Instead of fine-tuning model weights, we optimized performance through rigorous prompt engineering and logical constraint injection.

## 2. Methodology Exploration

Our technical exploration focused on four key areas to address the complexity of network log analysis:

### 2.1 Rule-Based Engines (The Backbone)
We developed a comprehensive rule engine based on 3GPP standards and expert experience.
- **Role**: Serves as a pre-filter and consistency checker.
- **Implementation**: Hard-coded logic detects specific patterns such as:
  - *Neighbor Cell Difference < 3dB* $\rightarrow$ **Overlap Coverage**.
  - *RSRP < -110dBm* $\rightarrow$ **Weak Coverage**.
  - *High A3 Offset* $\rightarrow$ **Delayed Handover**.
- **Impact**: Ensures that "physically impossible" answers are eliminated before the LLM processes the query.

### 2.2 RAG (Retrieval-Augmented Generation)
To leverage historical data strategies, we implemented RAG.
- **Implementation**: We constructed a vector/feature database from the training set. When a new problem arrives, the system retrieves relevant historical cases with known root causes.
- **Benefit**: Provides the LLM with few-shot examples that are contextually similar to the current problem, significantly improving diagnosis accuracy for rare failure modes.

### 2.3 KNN (K-Nearest Neighbors)
We utilized KNN as the retrieval mechanism for our RAG system.
- **Feature Extraction**: We extract numeric vectors from unstructured logs (e.g., `[min_RSRP, avg_SINR, max_Speed, handover_count]`).
- **Matching**: KNN identifies the top-K most similar historical scenarios based on these feature vectors. This statistical similarity guides the Logic Engine in cases where explicit rules are ambiguous.

### 2.4 Quantization
We explored model quantization techniques to balance performance and resource usage.
- **Exploration**: Tested 4-bit and 8-bit quantization for local deployment feasibility.
- **Outcome**: While our final submission relies on the Qwen3-32B API, the insights gained from analyzing quantization sensitivity helped us understand which features (e.g., specific numerical precision in signal values) were most critical for the model's attention.

## 3. Final Proposed Architecture

Our final solution is a **Hybrid Neuro-Symbolic System**:

1.  **Logical Analysis Layer**: 
    -   Extracts structured features from the problem description.
    -   Performs a logical analysis of the provided options against the data.
    -   Filters options that contradict physical laws of signal propagation.
    
2.  **LLM Inference Layer (Qwen/Qwen3-32B API)**:
    -   **No Fine-Tuning**: We did not update the model weights.
    -   **Prompt Strategy**: We refined our prompts through iterative testing. The prompt includes the filtered options, key extracted features, and the logical constraints. This guides the LLM toward physically plausible solutions.

## 4. Performance & Validation

We validated our approach extensively using the provided Training data and Phase 1 Test data.

| Dataset | Performance |
| :--- | :--- |
| **Phase 1 Validation** | Achieved **>98%** accuracy. |
| **Combined (Train + Phase 1)** | Stabilized at **~97.1%** accuracy. |

## 5. Conclusion

We present a single final entry that represents the culmination of our research into combining rule-based determinism with large language model reasoning. By strictly adhering to telecom domain principles and employing statistical logic (KNN/RAG), we achieved high stability and accuracy without the need for model fine-tuning.
