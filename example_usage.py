"""
Example Usage: Running MYE Experiments with SLO Listings

This script demonstrates the complete workflow for testing
SLO-generated listings on Amazon MYE.
"""
from mye_experiment_runner import MYEExperimentRunner
from lqs_integration import LQSIntegration


def example_1_basic_experiment():
    """
    Example 1: Run a basic Title experiment
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Title Experiment")
    print("="*60 + "\n")

    runner = MYEExperimentRunner(headless=False)

    result = runner.run_experiment(
        asin="B01EXAMPLE",
        control_title="Old Product Title Here Without Optimization",
        treatment_title="Premium Wireless Headphones | Noise Cancelling | 40Hr Battery | Comfortable Design",
        duration_days=28
    )

    print("\nResult:")
    print(f"Status: {result['status']}")
    if result['status'] == 'RUNNING':
        print(f"Experiment ID: {result['experiment_id']}")
        print(f"LQS Score: {result['lqs_validation']['lqs']}")
        print(f"Grade: {result['lqs_validation']['grade']}")
    elif result['status'] == 'BLOCKED':
        print(f"Reason: {result['reason']}")


def example_2_lqs_validation_only():
    """
    Example 2: Validate listing with LQS without creating experiment
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: LQS Validation Only")
    print("="*60 + "\n")

    lqs = LQSIntegration()

    listing_data = {
        "title": "Premium Wireless Headphones | Noise Cancelling | 40Hr Battery Life | Over-Ear Design",
        "bullets": [
            "Advanced noise cancellation technology eliminates 99% of background noise",
            "Extended 40-hour battery life with fast charging support",
            "Comfortable over-ear design with memory foam padding",
            "Premium audio drivers deliver crystal-clear sound quality",
            "Universal Bluetooth 5.0 connectivity with all devices"
        ],
        "description": "Experience premium audio quality..."
    }

    result = lqs.calculate_lqs("B01EXAMPLE", listing_data)

    print("LQS Score:", result["lqs"])
    print("Grade:", result["grade"])
    print("MYE Eligible:", result["mye_eligible"])
    print("\nDimension Breakdown:")
    for dim_name, dim_data in result["dimensions"].items():
        print(f"  {dim_name}: {dim_data['score']}/100 (weight: {dim_data['weight']*100}%)")


def example_3_validate_before_experiment():
    """
    Example 3: Pre-validate, then only run experiment if passes
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Pre-validate Before Creating Experiment")
    print("="*60 + "\n")

    lqs = LQSIntegration()

    treatment_data = {
        "title": "Test Product Title",  # Intentionally short to fail
        "bullets": [],
        "description": ""
    }

    # Pre-validate
    validation = lqs.validate_for_mye("B01EXAMPLE", treatment_data)

    print(f"LQS Score: {validation['lqs']}")
    print(f"MYE Eligible: {validation['eligible']}")

    if not validation["eligible"]:
        print("\n❌ Listing does not meet MYE eligibility criteria")
        print("\nBlockers:")
        for blocker in validation["blockers"]:
            print(f"  - {blocker}")
        print("\nRecommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")
        print("\nExperiment NOT created")
        return

    print("\n✓ Listing passes - proceeding to create experiment...")

    runner = MYEExperimentRunner(headless=False)
    result = runner.run_experiment(
        asin="B01EXAMPLE",
        control_title="Old Title",
        treatment_title=treatment_data["title"],
        duration_days=28
    )

    print(f"Experiment Status: {result['status']}")


def example_4_collect_metrics():
    """
    Example 4: Collect metrics for an existing experiment
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Collect Experiment Metrics")
    print("="*60 + "\n")

    runner = MYEExperimentRunner(headless=False)

    # Replace with actual experiment ID
    experiment_id = "EXP_123456"

    print(f"Collecting metrics for experiment: {experiment_id}")

    result = runner.collect_metrics(experiment_id)

    print("\nControl Variant:")
    print(f"  Impressions: {result['metrics']['control']['impressions']:,}")
    print(f"  Clicks: {result['metrics']['control']['clicks']:,}")
    print(f"  CTR: {result['metrics']['control']['ctr']}%")
    print(f"  Units Ordered: {result['metrics']['control']['units_ordered']:,}")
    print(f"  CVR: {result['metrics']['control']['cvr']}%")

    print("\nTreatment Variant:")
    print(f"  Impressions: {result['metrics']['treatment']['impressions']:,}")
    print(f"  Clicks: {result['metrics']['treatment']['clicks']:,}")
    print(f"  CTR: {result['metrics']['treatment']['ctr']}%")
    print(f"  Units Ordered: {result['metrics']['treatment']['units_ordered']:,}")
    print(f"  CVR: {result['metrics']['treatment']['cvr']}%")

    print("\nAnalysis:")
    print(f"  Winner: {result['analysis']['winner']}")
    print(f"  CTR Lift: {result['analysis']['ctr_lift_percent']}%")
    print(f"  CVR Lift: {result['analysis']['cvr_lift_percent']}%")
    print(f"  Recommendation: {result['analysis']['recommendation']}")
    print(f"  Confidence: {result['analysis']['confidence']}")


def example_5_generate_report():
    """
    Example 5: Generate comprehensive report
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Generate Experiment Report")
    print("="*60 + "\n")

    runner = MYEExperimentRunner(headless=False)

    # Replace with actual experiment ID
    experiment_id = "EXP_123456"

    report = runner.generate_report(experiment_id)

    print("Experiment Report")
    print("-" * 60)
    print(f"Experiment ID: {report['experiment_id']}")
    print(f"ASIN: {report['asin']}")
    print(f"Created: {report['created_at']}")
    print(f"\nLQS Score: {report['lqs_score']} ({report['lqs_grade']})")
    print(f"\nControl Title:\n  {report['control_title']}")
    print(f"\nTreatment Title:\n  {report['treatment_title']}")
    print(f"\nRecommendation: {report['recommendation']}")
    print(f"CTR Lift: {report['analysis']['ctr_lift_percent']}%")


def example_6_batch_experiments():
    """
    Example 6: Run experiments for multiple ASINs
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Processing Multiple ASINs")
    print("="*60 + "\n")

    runner = MYEExperimentRunner(headless=False)

    # List of ASINs to test
    test_cases = [
        {
            "asin": "B01EXAMPLE1",
            "control": "Old Title 1",
            "treatment": "Optimized Title 1 | Key Benefits | Brand"
        },
        {
            "asin": "B01EXAMPLE2",
            "control": "Old Title 2",
            "treatment": "Optimized Title 2 | Key Features | Brand"
        }
    ]

    results = []

    for case in test_cases:
        print(f"\nProcessing ASIN: {case['asin']}")

        result = runner.run_experiment(
            asin=case['asin'],
            control_title=case['control'],
            treatment_title=case['treatment'],
            duration_days=28
        )

        results.append({
            "asin": case['asin'],
            "status": result['status'],
            "experiment_id": result.get('experiment_id'),
            "lqs": result.get('lqs_validation', {}).get('lqs')
        })

        print(f"  Status: {result['status']}")

    print("\n" + "="*60)
    print("BATCH RESULTS SUMMARY")
    print("="*60)

    for r in results:
        status_icon = "✓" if r['status'] == 'RUNNING' else "❌"
        print(f"{status_icon} {r['asin']}: {r['status']} (LQS: {r['lqs']})")


def main():
    """
    Main menu for example selection
    """
    print("\n" + "="*60)
    print("SLO MYE Browser Automation - Example Usage")
    print("="*60)
    print("\nAvailable Examples:")
    print("1. Basic Title Experiment")
    print("2. LQS Validation Only")
    print("3. Pre-validate Before Experiment")
    print("4. Collect Experiment Metrics")
    print("5. Generate Experiment Report")
    print("6. Batch Process Multiple ASINs")
    print("\nTo run an example, uncomment the function call below")
    print("="*60 + "\n")

    # Uncomment the example you want to run:
    # example_1_basic_experiment()
    # example_2_lqs_validation_only()
    # example_3_validate_before_experiment()
    # example_4_collect_metrics()
    # example_5_generate_report()
    # example_6_batch_experiments()

    print("Edit example_usage.py to uncomment and run specific examples")


if __name__ == "__main__":
    main()
