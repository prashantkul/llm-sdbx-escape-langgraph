"""
DeepEval Integration for Prompt Library

Saves attack prompts to DeepEval platform for tracking and analysis.
"""

from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# DeepEval uses CONFIDENT_API_KEY (not CONFIDENT_AI_API_KEY)
# If user set CONFIDENT_AI_API_KEY, copy it to CONFIDENT_API_KEY
if 'CONFIDENT_AI_API_KEY' in os.environ and 'CONFIDENT_API_KEY' not in os.environ:
    os.environ['CONFIDENT_API_KEY'] = os.environ['CONFIDENT_AI_API_KEY']

# DeepEval imports for Confident AI integration
try:
    from deepeval.test_case import LLMTestCase
    from deepeval.dataset import EvaluationDataset, Golden
    import deepeval
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False


class PromptLibrary:
    """
    Manages attack prompts using DeepEval for tracking and evaluation.
    """

    def __init__(self, library_name: str = "llm-attack-prompts"):
        """
        Initialize prompt library.

        Args:
            library_name: Name for the prompt library
        """
        self.library_name = library_name
        self.prompts: List[Dict] = []

    def add_attack_prompt(
        self,
        prompt: str,
        strategy_name: str,
        category: str,
        target_goal: str,
        victim_response: str,
        success: bool,
        turn_number: int,
        method: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Add an attack prompt to the library.

        Args:
            prompt: The attack prompt text
            strategy_name: Name of the attack strategy
            category: Strategy category
            target_goal: What the attack was trying to achieve
            victim_response: How the victim responded
            success: Whether the attack succeeded
            turn_number: Which turn in the conversation
            method: "template" or "adaptive"
            metadata: Additional metadata
        """
        prompt_data = {
            "prompt": prompt,
            "strategy": strategy_name,
            "category": category,
            "target_goal": target_goal,
            "victim_response": victim_response,
            "success": success,
            "turn": turn_number,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        self.prompts.append(prompt_data)

    def import_from_results_file(self, results_file: Path):
        """
        Import prompts from an attack results JSON file.

        Args:
            results_file: Path to attack results JSON
        """
        with open(results_file, 'r') as f:
            data = json.load(f)

        for result in data.get("results", []):
            strategy_name = result.get("strategy", "Unknown")
            category = result.get("category", "Unknown")
            target_goal = result.get("goal", "Unknown")

            for turn in result.get("turns", []):
                self.add_attack_prompt(
                    prompt=turn.get("attack_prompt", ""),
                    strategy_name=strategy_name,
                    category=category,
                    target_goal=target_goal,
                    victim_response=turn.get("victim_response", ""),
                    success=turn.get("analysis", {}).get("success", False),
                    turn_number=turn.get("turn", 0),
                    method=turn.get("method", "unknown"),
                    metadata={
                        "blocked": turn.get("analysis", {}).get("blocked", False),
                        "error": turn.get("analysis", {}).get("error", False),
                        "reasoning": turn.get("analysis", {}).get("reasoning", ""),
                    }
                )

    def import_all_results(self, results_dir: Path = None):
        """
        Import all attack results from the results directory.

        Args:
            results_dir: Directory containing attack results
        """
        if results_dir is None:
            results_dir = Path(__file__).parent / "llm_attacker_framework" / "results"

        results_dir = Path(results_dir)

        for results_file in results_dir.glob("*.json"):
            print(f"Importing prompts from {results_file.name}...")
            self.import_from_results_file(results_file)

        print(f"\n✅ Imported {len(self.prompts)} attack prompts to library")

    def save_library(self, filepath: str = None):
        """
        Save the prompt library to a JSON file.

        Args:
            filepath: Path to save library
        """
        if filepath is None:
            filepath = f"prompt_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Save as JSON
        library_dict = {
            "library_name": self.library_name,
            "total_prompts": len(self.prompts),
            "created_at": datetime.now().isoformat(),
            "prompts": self.prompts,
        }

        with open(filepath, 'w') as f:
            json.dump(library_dict, f, indent=2)

        print(f"\n💾 Saved prompt library to: {filepath}")
        return filepath

    def get_statistics(self) -> Dict:
        """
        Get statistics about the prompt library.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_prompts": len(self.prompts),
            "by_strategy": {},
            "by_category": {},
            "by_method": {},
            "success_rate": 0,
        }

        successful = 0

        for p in self.prompts:
            # Count by strategy
            strategy = p.get("strategy", "Unknown")
            if strategy not in stats["by_strategy"]:
                stats["by_strategy"][strategy] = {"total": 0, "successful": 0}
            stats["by_strategy"][strategy]["total"] += 1

            # Count by category
            category = p.get("category", "Unknown")
            if category not in stats["by_category"]:
                stats["by_category"][category] = {"total": 0, "successful": 0}
            stats["by_category"][category]["total"] += 1

            # Count by method
            method = p.get("method", "Unknown")
            if method not in stats["by_method"]:
                stats["by_method"][method] = {"total": 0, "successful": 0}
            stats["by_method"][method]["total"] += 1

            # Track success
            if p.get("success", False):
                successful += 1
                stats["by_strategy"][strategy]["successful"] += 1
                stats["by_category"][category]["successful"] += 1
                stats["by_method"][method]["successful"] += 1

        stats["success_rate"] = (successful / len(self.prompts) * 100) if self.prompts else 0

        return stats

    def print_statistics(self):
        """Print library statistics."""
        stats = self.get_statistics()

        print("\n" + "="*80)
        print("PROMPT LIBRARY STATISTICS")
        print("="*80)
        print(f"Total Prompts: {stats['total_prompts']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print()

        print("BY STRATEGY:")
        print("-" * 80)
        for strategy, data in stats['by_strategy'].items():
            rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {strategy:40s}: {data['successful']:2d}/{data['total']:2d} ({rate:5.1f}%)")
        print()

        print("BY CATEGORY:")
        print("-" * 80)
        for category, data in stats['by_category'].items():
            rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {category:30s}: {data['successful']:2d}/{data['total']:2d} ({rate:5.1f}%)")
        print()

        print("BY METHOD:")
        print("-" * 80)
        for method, data in stats['by_method'].items():
            rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"  {method:20s}: {data['successful']:2d}/{data['total']:2d} ({rate:5.1f}%)")
        print("="*80)

    def get_prompts_by_category(self, category: str) -> List[Dict]:
        """
        Get all prompts for a specific category.

        Args:
            category: Category name

        Returns:
            List of prompts
        """
        return [p for p in self.prompts if p.get("category") == category]

    def get_successful_prompts(self) -> List[Dict]:
        """
        Get all successful attack prompts.

        Returns:
            List of successful prompts
        """
        return [p for p in self.prompts if p.get("success", False)]

    def export_to_markdown(self, filepath: str = None):
        """
        Export prompt library to a markdown file for easy reading.

        Args:
            filepath: Path to save markdown file
        """
        if filepath is None:
            filepath = f"prompt_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        stats = self.get_statistics()

        with open(filepath, 'w') as f:
            f.write("# LLM Attack Prompt Library\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Statistics\n\n")
            f.write(f"- **Total Prompts**: {stats['total_prompts']}\n")
            f.write(f"- **Success Rate**: {stats['success_rate']:.1f}%\n\n")

            # By category
            f.write("### By Category\n\n")
            for category, data in stats['by_category'].items():
                rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                f.write(f"- **{category}**: {data['successful']}/{data['total']} ({rate:.1f}%)\n")
            f.write("\n")

            # By method
            f.write("### By Method\n\n")
            for method, data in stats['by_method'].items():
                rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                f.write(f"- **{method}**: {data['successful']}/{data['total']} ({rate:.1f}%)\n")
            f.write("\n")

            # All prompts organized by category
            f.write("## Prompts by Category\n\n")

            categories = set(p.get("category", "Unknown") for p in self.prompts)

            for category in sorted(categories):
                f.write(f"### {category}\n\n")

                prompts = self.get_prompts_by_category(category)

                for i, p in enumerate(prompts, 1):
                    f.write(f"#### Prompt {i}\n\n")
                    f.write(f"- **Strategy**: {p.get('strategy', 'Unknown')}\n")
                    f.write(f"- **Method**: {p.get('method', 'Unknown')}\n")
                    f.write(f"- **Turn**: {p.get('turn', '?')}\n")
                    f.write(f"- **Success**: {'✅ Yes' if p.get('success') else '❌ No'}\n")
                    f.write(f"- **Blocked**: {'Yes' if p.get('blocked') else 'No'}\n\n")
                    f.write("**Prompt:**\n```\n")
                    f.write(p["prompt"])
                    f.write("\n```\n\n")
                    f.write("---\n\n")

        print(f"\n📄 Exported prompt library to markdown: {filepath}")
        return filepath

    def push_to_confident_ai(self, project_name: str = "My first project"):
        """
        Push prompts to Confident AI platform using DeepEval.

        Args:
            project_name: Name of the Confident AI project
        """
        if not DEEPEVAL_AVAILABLE:
            print("❌ DeepEval not available. Install with: pip install deepeval")
            return

        print(f"\n☁️  Pushing {len(self.prompts)} prompts to Confident AI project '{project_name}'...")

        # Convert prompts to DeepEval Goldens
        goldens = []
        for p in self.prompts:
            golden = Golden(
                input=p["prompt"],
                actual_output=p.get("victim_response", "")[:500],  # Truncate long responses
                expected_output="Attack should be blocked by security controls",
                context=[p.get("target_goal", "")],
                retrieval_context=[
                    f"Strategy: {p.get('strategy', 'Unknown')}",
                    f"Category: {p.get('category', 'Unknown')}",
                    f"Turn: {p.get('turn', '?')}",
                    f"Method: {p.get('method', 'Unknown')}",
                ],
                additional_metadata={
                    "strategy": p.get("strategy", "Unknown"),
                    "category": p.get("category", "Unknown"),
                    "success": p.get("success", False),
                    "blocked": p.get("blocked", False),
                    "turn": p.get("turn", 0),
                    "method": p.get("method", "Unknown"),
                }
            )
            goldens.append(golden)

        # Create dataset and push to Confident AI
        try:
            # Create dataset with goldens
            dataset = EvaluationDataset(goldens=goldens)

            # Push to Confident AI
            alias = f"attack-prompts-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            dataset.push(alias=alias)

            print(f"✅ Successfully pushed {len(goldens)} prompts to Confident AI!")
            print(f"   Dataset: {alias}")
            print(f"   View at: https://app.confident-ai.com/")
        except Exception as e:
            print(f"❌ Error pushing to Confident AI: {e}")
            print("   Make sure CONFIDENT_AI_API_KEY is set in your environment")
            import traceback
            traceback.print_exc()


def main(push_to_cloud: bool = True):
    """
    Build prompt library from all attack results.

    Args:
        push_to_cloud: Whether to push to Confident AI (requires CONFIDENT_AI_API_KEY)
    """
    print("\n🔨 Building Prompt Library...")
    print("="*80)

    # Create library
    library = PromptLibrary(library_name="llm-attack-prompts")

    # Import all results
    library.import_all_results()

    # Print statistics
    library.print_statistics()

    # Save library to JSON
    json_path = library.save_library()

    # Export to markdown
    md_path = library.export_to_markdown()

    print("\n✅ Prompt library built successfully!")
    print(f"   JSON: {json_path}")
    print(f"   Markdown: {md_path}")

    # Push to Confident AI if requested
    if push_to_cloud:
        library.push_to_confident_ai(project_name="My first project")

    return library


if __name__ == "__main__":
    main()
