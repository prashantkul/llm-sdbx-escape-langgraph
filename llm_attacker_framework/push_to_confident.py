"""
Push attack results to Confident AI without complex evaluation.

Just uploads the data for visualization and tracking.
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# DeepEval uses CONFIDENT_API_KEY
if 'CONFIDENT_AI_API_KEY' in os.environ and 'CONFIDENT_API_KEY' not in os.environ:
    os.environ['CONFIDENT_API_KEY'] = os.environ['CONFIDENT_AI_API_KEY']

from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset, Golden

from deepeval_integration import PromptLibrary


def main():
    """Push attack results to Confident AI."""

    print("\n" + "="*80)
    print("PUSH ATTACK RESULTS TO CONFIDENT AI")
    print("="*80)

    # Create library
    print("\n📚 Loading attack prompts...")
    library = PromptLibrary()
    library.import_all_results()
    print(f"✅ Loaded {len(library.prompts)} prompts")

    # Create goldens for Confident AI
    print("\n🔄 Converting to Confident AI format...")
    goldens = []

    for p in library.prompts:
        # Create analysis text
        analysis = []
        if p.get("blocked"):
            analysis.append("✅ Blocked by security controls")
        if p.get("success"):
            analysis.append("❌ Attack succeeded")
        if p.get("method") == "adaptive":
            analysis.append("🤖 Adaptive strategy")
        if p.get("turn", 0) > 1:
            analysis.append(f"🔄 Multi-turn (turn {p.get('turn')})")

        golden = Golden(
            input=p["prompt"],
            actual_output=p.get("victim_response", "")[:500],
            expected_output="Attack should be blocked",
            context=[
                p.get("target_goal", ""),
                " | ".join(analysis) if analysis else "Single turn attack"
            ],
            retrieval_context=[
                f"Strategy: {p.get('strategy', 'Unknown')}",
                f"Category: {p.get('category', 'Unknown')}",
                f"Method: {p.get('method', 'Unknown')}",
                f"Turn: {p.get('turn', 0)}",
            ],
            additional_metadata={
                "strategy": p.get("strategy", "Unknown"),
                "category": p.get("category", "Unknown"),
                "success": p.get("success", False),
                "blocked": p.get("blocked", False),
                "turn": p.get("turn", 0),
                "method": p.get("method", "Unknown"),
                "timestamp": p.get("timestamp", ""),
            }
        )
        goldens.append(golden)

    print(f"✅ Created {len(goldens)} test cases")

    # Create dataset
    print("\n☁️  Pushing to Confident AI...")
    try:
        dataset = EvaluationDataset(goldens=goldens)

        alias = f"attack-eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        dataset.push(alias=alias)

        print(f"\n✅ Successfully pushed {len(goldens)} test cases to Confident AI!")
        print(f"   Dataset: {alias}")
        print(f"   View at: https://app.confident-ai.com/")

        # Print summary
        print("\n" + "="*80)
        print("📊 SUMMARY:")
        print("="*80)

        total = len(goldens)
        blocked = sum(1 for p in library.prompts if p.get("blocked"))
        successful = sum(1 for p in library.prompts if p.get("success"))
        adaptive = sum(1 for p in library.prompts if p.get("method") == "adaptive")
        multiturn = sum(1 for p in library.prompts if p.get("turn", 0) > 1)

        print(f"Total Attacks: {total}")
        print(f"Blocked: {blocked} ({blocked/total*100:.1f}%)")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Adaptive Prompts: {adaptive} ({adaptive/total*100:.1f}%)")
        print(f"Multi-turn: {multiturn} ({multiturn/total*100:.1f}%)")

        # By category
        from collections import defaultdict
        by_category = defaultdict(int)
        for p in library.prompts:
            by_category[p.get("category", "Unknown")] += 1

        print("\nBy Category:")
        for cat, count in sorted(by_category.items()):
            print(f"  {cat:30s}: {count:2d} ({count/total*100:5.1f}%)")

        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
