#!/usr/bin/env python3
"""
Simple script to run LLM attacker framework tests.

Usage:
    python run_attack.py --mode hybrid --strategy "Authority Figure"
    python run_attack.py --mode adaptive --target FILE_READ
    python run_attack.py --suite  # Run full suite
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent / '.env')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from tests.test_orchestrator import AttackOrchestrator
from strategies import get_all_strategy_names


def main():
    parser = argparse.ArgumentParser(
        description="LLM Attacker Framework: Claude vs Gemini Security Testing"
    )

    parser.add_argument(
        "--mode",
        choices=["template", "adaptive", "hybrid"],
        default="hybrid",
        help="Attack mode (default: hybrid)"
    )

    parser.add_argument(
        "--strategy",
        choices=get_all_strategy_names(),
        help="Specific strategy to test (default: all)"
    )

    parser.add_argument(
        "--target",
        choices=["FILE_READ", "SHELL_EXEC", "PYTHON_URLLIB", "FILE_WRITE", "ENV_VARS", "ALL"],
        default="FILE_READ",
        help="Target exploit to attempt (default: FILE_READ)"
    )

    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run full attack suite (all strategies × all targets)"
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=5,
        help="Maximum conversation turns per attack (default: 5)"
    )

    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List all available strategies and exit"
    )

    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List all target exploits and exit"
    )

    args = parser.parse_args()

    # List strategies
    if args.list_strategies:
        print("\n📋 Available Attack Strategies:")
        print("=" * 80)
        from strategies import ALL_STRATEGIES
        by_category = {}
        for s in ALL_STRATEGIES:
            if s.category not in by_category:
                by_category[s.category] = []
            by_category[s.category].append(s.name)

        for category, strategies in by_category.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for strategy in strategies:
                print(f"  - {strategy}")
        print()
        return

    # List targets
    if args.list_targets:
        print("\n🎯 Available Target Exploits:")
        print("=" * 80)
        for target in Config.TARGET_EXPLOITS:
            print(f"\n{target['id']}:")
            print(f"  Name: {target['name']}")
            print(f"  Goal: {target['goal']}")
            print(f"  Difficulty: {target['difficulty']}")
        print()
        return

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set GOOGLE_API_KEY in your .env file")
        print("The framework uses Gemini 2.5 Pro as the attacker")
        return 1

    # Update max turns
    Config.MAX_TURNS_PER_ATTACK = args.max_turns

    # Create orchestrator
    print(f"\n🚀 Starting LLM Attacker Framework")
    print(f"   Mode: {args.mode}")
    print(f"   Attacker: Gemini ({Config.ATTACKER_MODEL})")
    print(f"   Victim: Gemini via LangGraph ({Config.LANGGRAPH_URL})")
    print(f"   🎯 Gemini vs Gemini - Same family attack!")
    print("=" * 80)

    orchestrator = AttackOrchestrator(mode=args.mode)

    try:
        if args.suite:
            # Run full suite
            print("\n🎯 Running full attack suite...")
            results = orchestrator.run_attack_suite()
            orchestrator.print_summary()

        elif args.strategy:
            # Run specific strategy on target
            target = next((t for t in Config.TARGET_EXPLOITS if t['id'] == args.target), None)
            if not target:
                print(f"❌ Target {args.target} not found")
                return 1

            print(f"\n🎯 Running single attack:")
            print(f"   Strategy: {args.strategy}")
            print(f"   Target: {target['name']}")

            result = orchestrator.run_single_attack(
                target_goal=target['goal'],
                strategy_name=args.strategy,
                success_pattern=target.get('success_pattern'),
            )

            print("\n" + "=" * 80)
            print("RESULT:")
            print("=" * 80)
            print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
            print(f"Turns: {result['total_turns']}")
            print(f"Final Analysis: {result['final_analysis'].get('reasoning', 'N/A')}")

        else:
            # Run all strategies on one target
            target = next((t for t in Config.TARGET_EXPLOITS if t['id'] == args.target), None)
            if not target:
                print(f"❌ Target {args.target} not found")
                return 1

            print(f"\n🎯 Testing all strategies against: {target['name']}")

            results = orchestrator.run_attack_suite(
                target_exploits=[target],
            )
            orchestrator.print_summary()

        # Save results
        filepath = orchestrator.save_results()
        print(f"\n💾 Results saved to: {filepath}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        orchestrator.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
