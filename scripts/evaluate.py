"""
run a fixed set of questions against a deployed session and record keyword coverage
and latency for each answer.

usage: LENS_API_BASE=https://<api-id>.execute-api.<region>.amazonaws.com/Prod \
       python scripts/evaluate.py <session_id>
"""

import json
import os
import sys

import requests

RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_results.json")

# test questions and keywords we expect in a good answer
TEST_CASES = [
    ("What is the termination clause?", ["terminate", "termination", "notice", "days"]),
    ("Who are the parties in this agreement?", ["party", "parties", "agreement", "between"]),
    ("What is the effective date?", ["date", "effective", "commence"]),
    ("What are the payment terms?", ["payment", "pay", "amount", "fee"]),
    ("What is the confidentiality clause?", ["confidential", "disclose", "information"]),
]


def run_query(api_base, session_id, question):
    response = requests.post(
        f"{api_base}/query",
        json={"sessionId": session_id, "query": question},
        timeout=60,
    )
    return response.json()


def keyword_coverage(answer, expected_keywords):
    """fraction of the expected keywords that appear in the answer"""
    answer_lower = answer.lower()
    matches = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return matches / len(expected_keywords) if expected_keywords else 0


def evaluate_session(api_base, session_id, test_cases=TEST_CASES):
    results = {
        "session_id": session_id,
        "total_queries": 0,
        "successful_queries": 0,
        "coverage_scores": [],
        "latencies_ms": [],
        "metrics_breakdown": [],
    }

    print(f"\nevaluating session: {session_id}")
    print("-" * 50)

    for question, expected_keywords in test_cases:
        results["total_queries"] += 1
        try:
            response = run_query(api_base, session_id, question)
        except requests.RequestException as e:
            print(f"q: {question[:40]}... ERROR: {e}")
            continue

        if "answer" not in response:
            print(f"q: {question[:40]}... FAILED: {response}")
            continue

        metrics = response.get("metrics", {})
        coverage = keyword_coverage(response["answer"], expected_keywords)
        latency = metrics.get("total_time_ms", 0)

        results["successful_queries"] += 1
        results["coverage_scores"].append(coverage)
        results["latencies_ms"].append(latency)
        results["metrics_breakdown"].append({
            "question": question,
            "coverage": coverage,
            "latency_ms": latency,
            "embedding_ms": metrics.get("embedding_time_ms"),
            "search_ms": metrics.get("similarity_search_time_ms"),
            "llm_ms": metrics.get("llm_time_ms"),
            "similarity": metrics.get("top_chunk_similarity"),
        })

        print(f"q: {question[:40]}...")
        print(f"   keyword coverage: {coverage:.0%} | latency: {latency}ms")
        print(f"   similarity: {metrics.get('top_chunk_similarity', 'n/a')}")

    if results["coverage_scores"]:
        results["avg_coverage"] = sum(results["coverage_scores"]) / len(results["coverage_scores"])
        results["avg_latency_ms"] = sum(results["latencies_ms"]) / len(results["latencies_ms"])

        print("-" * 50)
        print(f"queries: {results['successful_queries']}/{results['total_queries']}")
        print(f"avg keyword coverage: {results['avg_coverage']:.1%}")
        print(f"avg latency: {results['avg_latency_ms']:.0f}ms")

    return results


def main():
    api_base = os.environ.get("LENS_API_BASE", "").rstrip("/")
    if len(sys.argv) < 2 or not api_base:
        print(__doc__.strip())
        print("\nget a session_id by uploading a document through the frontend and")
        print("reading the llamaGet response in the browser network tab")
        sys.exit(1)

    results = evaluate_session(api_base, sys.argv[1])

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nresults saved to {os.path.relpath(RESULTS_PATH)}")


if __name__ == "__main__":
    main()
