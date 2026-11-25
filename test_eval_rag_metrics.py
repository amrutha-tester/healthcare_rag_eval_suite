import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.models import GeminiModel, LocalModel
from deepeval.evaluate.configs import AsyncConfig,CacheConfig, ErrorConfig
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
load_dotenv()

os.environ["DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE"] = "180"
os.environ["DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"] = "600"

# File paths
EVAL_DIR = Path(__file__).resolve().parent/ "eval"
INPUT_PATH = EVAL_DIR / "eval_results.json"
OUTPUT_PATH = EVAL_DIR / "evaluated_results.jsonl"

# Configure LLM Model for evaluation
# api_key = os.getenv("GEMINI_API_KEY")
# judge_model = GeminiModel(
#     model="gemini-3.6-flash",
#     api_key = api_key ,
#     temperature=0,
# )
class GroqJudgeModel(LocalModel):
    def generate(self, *args, **kwargs):
        for attempt in range(4):
            time.sleep(1.5)
            try:
                return super().generate(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    time.sleep(10 * (attempt + 1))
                else:
                    raise

judge_model = GroqJudgeModel(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
)
# Load RAG outputs from eval_results.json
with INPUT_PATH.open("r", encoding="utf-8") as file:
    results = json.load(file)[:10] 

questions_for_eval =[]

# Collect questions and create test cases for evaluation
for i, result in enumerate(results, start=1):
    print(f"\nEvaluating test {i}/{len(results)}")

    context = result["context"]
    retrieval_context = context if isinstance(context, list) else [context]

    test_case = LLMTestCase(
        input = result["question"],
        actual_output = result["actual_answer"],
        expected_output = result["expected_answer"],
        retrieval_context = retrieval_context

    )
    questions_for_eval.append(test_case)

AnswerRelevancy = AnswerRelevancyMetric(threshold = 0.7, model = judge_model)
Faithfulness = FaithfulnessMetric(threshold = 0.7, model = judge_model)
ContextualRelevancy = ContextualRelevancyMetric(threshold = 0.7, model = judge_model)
CorrectnessMetric = GEval (
    name = "Correctness",
    criteria = (
        "Determine whether actual output is factually correct based on the expected output"
    ),
    evaluation_params= [
    SingleTurnParams.ACTUAL_OUTPUT,
    SingleTurnParams.EXPECTED_OUTPUT     
    ],
    threshold = 0.7,
    model = judge_model
)


evaluation_results = evaluate(
    test_cases= questions_for_eval,
    metrics=[
        AnswerRelevancy,
        Faithfulness,
        ContextualRelevancy,
        CorrectnessMetric
    ],
    async_config=AsyncConfig(run_async=False, throttle_value=4),
    cache_config=CacheConfig(write_cache=False),
    error_config=ErrorConfig(ignore_errors=True),
)

evaluated_results = []

for i, (original_result, test_result) in enumerate(
    zip(results, evaluation_results.test_results), start=1
):
    answer_relevancy_score = None
    faithfulness_score = None
    context_relevancy_score = None
    correctness_score = None

    for metric_data in test_result.metrics_data:
        metric_name = metric_data.name.lower()
        if "answer relevancy" in metric_name:
            answer_relevancy_score = metric_data.score
        elif "faithfulness" in metric_name:
            faithfulness_score = metric_data.score
        elif "contextual relevancy" in metric_name:
            context_relevancy_score = metric_data.score
        elif "correctness" in metric_name:
            correctness_score = metric_data.score

    evaluated_result = {
        **original_result,
        "answer_relevancy": answer_relevancy_score,
        "faithfulness": faithfulness_score,
        "context_relevancy": context_relevancy_score,
        "correctness": correctness_score,
    }
    evaluated_results.append(evaluated_result)

    print(f"\nTest {i}/{len(results)} Metrics:")
    print("  Answer Relevancy: ", answer_relevancy_score)
    print("  Faithfulness:     ", faithfulness_score)
    print("  Context Relevancy:", context_relevancy_score)
    print("  Correctness:      ", correctness_score)

with OUTPUT_PATH.open("w", encoding="utf-8") as file:
    for item in evaluated_results:
        file.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nDone! Results saved to {OUTPUT_PATH}")