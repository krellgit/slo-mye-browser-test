"""
MYE Experiment Runner
Orchestrates the full flow: LQS validation -> MYE experiment creation -> Results collection
"""
import json
import os
from typing import Dict, List
from datetime import datetime
from amazon_mye_automation import AmazonMYEAutomation
from lqs_integration import LQSIntegration


class MYEExperimentRunner:
    """
    Orchestrates SLO listing testing on Amazon MYE

    Workflow:
    1. Load SLO-generated listing
    2. Validate with LQS (must be >= 70 for MYE eligibility)
    3. Create MYE experiment in Seller Central
    4. Monitor metrics daily
    5. Determine winner and apply
    """

    def __init__(self, headless: bool = False):
        self.lqs = LQSIntegration()
        self.headless = headless
        self.experiments_dir = "experiments"
        os.makedirs(self.experiments_dir, exist_ok=True)

    def run_experiment(self,
                      asin: str,
                      control_title: str,
                      treatment_title: str,
                      duration_days: int = 28) -> Dict:
        """
        Run complete MYE experiment workflow

        Args:
            asin: Product ASIN
            control_title: Current listing title (control variant)
            treatment_title: SLO-optimized title (treatment variant)
            duration_days: Experiment duration

        Returns:
            Experiment results dict
        """
        print(f"\n{'='*60}")
        print(f"MYE Experiment Runner - ASIN {asin}")
        print(f"{'='*60}\n")

        # Step 1: Validate treatment with LQS
        print("Step 1: Validating treatment listing with LQS...")
        treatment_data = {
            "title": treatment_title,
            "bullets": [],  # Title-only test
            "description": ""
        }

        lqs_validation = self.lqs.validate_for_mye(asin, treatment_data)

        print(f"  LQS Score: {lqs_validation['lqs']}/100")
        print(f"  Grade: {lqs_validation['grade']}")
        print(f"  MYE Eligible: {lqs_validation['eligible']}")

        if not lqs_validation["eligible"]:
            print("\n❌ Treatment listing FAILS MYE eligibility check")
            print("Blockers:")
            for blocker in lqs_validation["blockers"]:
                print(f"  - {blocker}")
            print("\nRecommendations:")
            for rec in lqs_validation["recommendations"]:
                print(f"  - {rec}")
            return {
                "status": "BLOCKED",
                "reason": "LQS below MYE threshold",
                "lqs_validation": lqs_validation
            }

        print("✓ Treatment listing passes MYE eligibility check\n")

        # Step 2: Create MYE experiment
        print("Step 2: Creating MYE experiment in Seller Central...")

        with AmazonMYEAutomation(headless=self.headless) as mye:
            # Login
            print("  Logging in to Seller Central...")
            mye.login()

            # Create experiment
            experiment_metadata = mye.create_experiment(
                asin=asin,
                attribute="TITLE",
                control_text=control_title,
                treatment_text=treatment_title,
                duration_days=duration_days
            )

            print(f"✓ Experiment created: {experiment_metadata['experiment_id']}\n")

            # Save experiment metadata
            self._save_experiment(experiment_metadata, lqs_validation)

        return {
            "status": "RUNNING",
            "experiment_id": experiment_metadata["experiment_id"],
            "lqs_validation": lqs_validation,
            "experiment_metadata": experiment_metadata
        }

    def collect_metrics(self, experiment_id: str) -> Dict:
        """
        Collect daily metrics for an experiment

        Args:
            experiment_id: MYE experiment ID

        Returns:
            Metrics dict
        """
        print(f"\nCollecting metrics for experiment {experiment_id}...")

        with AmazonMYEAutomation(headless=self.headless) as mye:
            mye.login()
            metrics = mye.get_experiment_metrics(experiment_id)

            # Determine winner
            analysis = mye.determine_winner(metrics)

            print(f"Control CTR: {metrics['control']['ctr']}%")
            print(f"Treatment CTR: {metrics['treatment']['ctr']}%")
            print(f"CTR Lift: {analysis['ctr_lift_percent']}%")
            print(f"Winner: {analysis['winner']}")
            print(f"Recommendation: {analysis['recommendation']}")

            # Save metrics
            self._save_metrics(experiment_id, metrics, analysis)

            return {
                "metrics": metrics,
                "analysis": analysis
            }

    def list_experiments(self) -> List[Dict]:
        """
        List all experiments

        Returns:
            List of experiment metadata
        """
        with AmazonMYEAutomation(headless=self.headless) as mye:
            mye.login()
            experiments = mye.get_all_experiments()
            return experiments

    def generate_report(self, experiment_id: str) -> Dict:
        """
        Generate comprehensive report for an experiment

        Args:
            experiment_id: MYE experiment ID

        Returns:
            Report dict
        """
        # Load experiment data
        experiment_file = os.path.join(self.experiments_dir, f"{experiment_id}.json")

        if not os.path.exists(experiment_file):
            return {"error": f"Experiment {experiment_id} not found"}

        with open(experiment_file, "r") as f:
            data = json.load(f)

        # Collect latest metrics
        latest_metrics = self.collect_metrics(experiment_id)

        report = {
            "experiment_id": experiment_id,
            "asin": data["metadata"]["asin"],
            "created_at": data["metadata"]["created_at"],
            "lqs_score": data["lqs_validation"]["lqs"],
            "lqs_grade": data["lqs_validation"]["grade"],
            "control_title": data["metadata"]["control_text"],
            "treatment_title": data["metadata"]["treatment_text"],
            "metrics": latest_metrics["metrics"],
            "analysis": latest_metrics["analysis"],
            "recommendation": latest_metrics["analysis"]["recommendation"],
            "generated_at": datetime.now().isoformat()
        }

        # Save report
        report_file = os.path.join(self.experiments_dir, f"{experiment_id}_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Report saved: {report_file}")

        return report

    def _save_experiment(self, metadata: Dict, lqs_validation: Dict) -> None:
        """Save experiment metadata to file"""
        experiment_id = metadata["experiment_id"]
        filepath = os.path.join(self.experiments_dir, f"{experiment_id}.json")

        data = {
            "metadata": metadata,
            "lqs_validation": lqs_validation,
            "metrics_history": []
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  Experiment data saved: {filepath}")

    def _save_metrics(self, experiment_id: str, metrics: Dict, analysis: Dict) -> None:
        """Append metrics to experiment file"""
        filepath = os.path.join(self.experiments_dir, f"{experiment_id}.json")

        if not os.path.exists(filepath):
            print(f"Warning: Experiment file not found: {filepath}")
            return

        with open(filepath, "r") as f:
            data = json.load(f)

        # Append metrics
        data["metrics_history"].append({
            "collected_at": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis
        })

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  Metrics saved to: {filepath}")


def main():
    """Example usage"""
    runner = MYEExperimentRunner(headless=False)

    # Example: Run experiment
    result = runner.run_experiment(
        asin="B01EXAMPLE",
        control_title="Old Product Title Here",
        treatment_title="Optimized Product Title with Key Benefits | Brand Name",
        duration_days=28
    )

    if result["status"] == "RUNNING":
        experiment_id = result["experiment_id"]
        print(f"\nExperiment {experiment_id} is now running!")
        print("Monitor metrics with: runner.collect_metrics(experiment_id)")


if __name__ == "__main__":
    main()
