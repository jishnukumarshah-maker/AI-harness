**Agentic Harness (v1.2)** is an explainable, self-correcting LLM reliability and semantic caching framework built in Python. Instead of blindly returning a raw language model response, it acts as a quality-assurance wrapper around Groq’s `llama-3.1-8b-instant` model—validating outputs, grading them with an AI critic, retrying failed attempts with corrective feedback, and caching high-scoring responses locally.

---

### Core Architecture & File Breakdown

| File | Purpose |
| --- | --- |
| **`harness.py`** | **Core Orchestrator (`run_harness`)**: Manages the 3-step lifecycle: checking the semantic cache, running the iterative generation-and-retry loop (up to `max_retries=2`), and logging results.

 |
| **`cache.py`** | **Semantic Cache & Telemetry**: Uses SQLite (`harness_cache.db`) and `SentenceTransformer` (`all-MiniLM-L6-v2`) to store vector embeddings of prompts and retrieve past answers via cosine similarity.

 |
| **`app.py`** | **Streamlit Web UI**: Provides a **Live Playground** (to test prompts and inspect step-by-step evaluation traces) and a **Reliability Analytics** dashboard (charting score gains and cache hit rates).

 |
| **`benchmark.py`** | **54-Sample Evaluation Suite**: Stress-tests the system across 3 categories (18 Strict JSON, 18 Strict Length/Bullet constraints, and 18 Code/Logic precision prompts) to generate resume-ready performance metrics.

 |
| **`main.py`** | **CLI Entry Point**: Runs single prompts from the terminal and prints the final answer, reliability scores, latency, and execution trace.

 |

---

### How the Pipeline Works

1. **Semantic Cache Lookup (`check_cache`)**:
* Encodes the incoming prompt into a dense vector using `all-MiniLM-L6-v2` and compares it against stored SQLite prompts using **cosine similarity**.


* If a match has $\ge 0.88$ (88%) similarity, it bypasses the LLM API entirely and returns the cached response immediately.




2. **Deterministic Rule Gate (`deterministic_validate`)**:
* Runs fast, zero-AI checks on the generated output: verifies the response is at least 15 characters long and, if `"json"` is mentioned in the prompt, extracts `{...}` and validates it with `json.loads()`.


* Failing deterministic rules immediately assigns a `0.30` score without wasting a critic API call.




3. **LLM-as-a-Judge Critic (`critic_evaluate`)**:
* Prompts `llama-3.1-8b-instant` to act as a strict QA critic, outputting a JSON object containing a `score` (`0.0` to `1.0`) and actionable `feedback`.




4. **Autonomous Self-Correction Loop**:
* If `score >= 0.80`, the loop terminates early.


* If `score < 0.80`, the harness appends the failed output and the critic's feedback back into the chat history and prompts the model to fix its mistakes (up to 2 retries).




5. **Selective Caching (`save_to_cache`)**:
* Only responses achieving a final reliability score of $\ge 0.80$ are persisted to the SQLite `responses` table so low-quality outputs never pollute the cache.





---

### Tracked & Computed Metrics

Across `app.py`, `cache.py`, and `benchmark.py`, the framework tracks and computes the following metrics:

* **Initial Score (`initial_score`)**: The reliability score (`0.00` – `1.00`) assigned to the model's very first generation attempt before any self-correction.


* **Final Reliability Score (`final_score`)**: The score after the retry loop finishes, alongside the **Score Delta** (`final_score - initial_score`).


* **Pass Rate Improvement**: The percentage of benchmark prompts scoring $\ge 0.80$ on Attempt 1 versus after retries (`init_pass_rate` $\rightarrow$ `final_pass_rate`).


* **Relative Reliability Gain (%)**: Computed as $\frac{\text{Mean Final Score} - \text{Mean Initial Score}}{\text{Mean Initial Score}} \times 100$.


* **Autonomous Error Recovery Rate (%)**: Percentage of initially failing prompts ($< 0.80$) that were successfully repaired to $\ge 0.80$ during the retry loop.


* **Retries Used & Average Retries/Query**: Number of correction cycles triggered (`0` to `2` per prompt).


* **Semantic Similarity Score**: Cosine similarity (`0.88` to `1.00`) between a new prompt and its matched cached query.


* **Cache Hit Rate (%)**: Percentage of total logged queries served directly from `harness_cache.db` without making live Groq API calls.


* **Latency & Speedup Factor**: End-to-end execution time in milliseconds (`latency_ms`), comparing **Avg Live API Latency** against **Avg Cache Hit Latency** to compute the latency speedup multiplier (`avg_live_ms / avg_cache_ms`).




