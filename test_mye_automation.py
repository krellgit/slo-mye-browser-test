"""
Test suite for MYE automation

Tests the complete workflow:
1. LQS validation
2. Seller Central login
3. MYE experiment creation
4. Metrics collection
5. Winner determination
"""
import pytest
from amazon_mye_automation import AmazonMYEAutomation
from lqs_integration import LQSIntegration
from mye_experiment_runner import MYEExperimentRunner


class TestLQSIntegration:
    """Test LQS integration and validation"""

    def test_lqs_calculation(self):
        """1. Test LQS score calculation"""
        lqs = LQSIntegration()

        listing_data = {
            "title": "Premium Wireless Headphones with Noise Cancellation | 40Hr Battery | Comfortable Design",
            "bullets": [
                "Advanced noise cancellation eliminates background noise",
                "40-hour battery life for extended use",
                "Comfortable over-ear design for all-day wear",
                "Premium sound quality with deep bass",
                "Easy Bluetooth pairing with all devices"
            ],
            "description": "Experience premium audio..."
        }

        result = lqs.calculate_lqs("B01TEST", listing_data)

        assert "lqs" in result
        assert 0 <= result["lqs"] <= 100
        assert "dimensions" in result
        assert len(result["dimensions"]) == 6

    def test_mye_eligibility_pass(self):
        """2. Test MYE eligibility validation - passing"""
        lqs = LQSIntegration()

        # High-quality listing
        listing_data = {
            "title": "Premium Wireless Headphones | Noise Cancelling | 40Hr Battery | Comfortable Design for Travel",
            "bullets": [
                "Industry-leading noise cancellation technology eliminates 99% of background noise",
                "Extended 40-hour battery life with quick charge feature",
                "Ergonomic over-ear design with memory foam padding",
                "Premium audio drivers deliver crystal-clear sound",
                "Universal Bluetooth 5.0 connectivity with all devices"
            ],
            "description": "Experience premium audio..."
        }

        validation = lqs.validate_for_mye("B01TEST", listing_data)

        assert validation["lqs"] >= LQSIntegration.MYE_THRESHOLD
        assert validation["eligible"] is True
        assert validation["grade"] in ["A", "B", "C"]

    def test_mye_eligibility_fail(self):
        """3. Test MYE eligibility validation - failing"""
        lqs = LQSIntegration()

        # Low-quality listing
        listing_data = {
            "title": "Headphones",
            "bullets": ["Good sound"],
            "description": ""
        }

        validation = lqs.validate_for_mye("B01TEST", listing_data)

        assert validation["lqs"] < LQSIntegration.MYE_THRESHOLD
        assert validation["eligible"] is False
        assert len(validation["blockers"]) > 0

    def test_dimension_weights_sum_to_100(self):
        """4. Test dimension weights sum to 100%"""
        lqs = LQSIntegration()

        listing_data = {
            "title": "Test Title",
            "bullets": [],
            "description": ""
        }

        result = lqs.calculate_lqs("B01TEST", listing_data)

        total_weight = sum(
            dim["weight"] for dim in result["dimensions"].values()
        )

        assert abs(total_weight - 1.0) < 0.01  # Allow for floating point rounding


class TestAmazonMYEAutomation:
    """Test Amazon Seller Central automation"""

    @pytest.mark.skip(reason="Requires valid Amazon credentials")
    def test_login(self):
        """5. Test Seller Central login"""
        with AmazonMYEAutomation(headless=True) as mye:
            result = mye.login()
            assert result is True

    @pytest.mark.skip(reason="Requires valid Amazon credentials and will create real experiment")
    def test_create_experiment(self):
        """6. Test MYE experiment creation"""
        with AmazonMYEAutomation(headless=False) as mye:
            mye.login()

            metadata = mye.create_experiment(
                asin="B01TEST",
                attribute="TITLE",
                control_text="Old Product Title",
                treatment_text="Optimized Product Title | Key Benefits | Brand",
                duration_days=28,
                traffic_split=50
            )

            assert "experiment_id" in metadata
            assert metadata["asin"] == "B01TEST"
            assert metadata["status"] == "RUNNING"

    def test_winner_determination_treatment_wins(self):
        """7. Test winner determination - treatment wins"""
        mye = AmazonMYEAutomation(headless=True)

        metrics = {
            "control": {
                "impressions": 10000,
                "clicks": 200,
                "ctr": 2.0,
                "units_ordered": 20,
                "cvr": 10.0
            },
            "treatment": {
                "impressions": 10000,
                "clicks": 250,
                "ctr": 2.5,
                "units_ordered": 30,
                "cvr": 12.0
            }
        }

        analysis = mye.determine_winner(metrics)

        assert analysis["winner"] == "TREATMENT"
        assert analysis["ctr_lift_percent"] == 25.0  # 25% improvement
        assert analysis["recommendation"] == "APPLY"

    def test_winner_determination_control_wins(self):
        """8. Test winner determination - control wins"""
        mye = AmazonMYEAutomation(headless=True)

        metrics = {
            "control": {
                "impressions": 10000,
                "clicks": 250,
                "ctr": 2.5,
                "units_ordered": 30,
                "cvr": 12.0
            },
            "treatment": {
                "impressions": 10000,
                "clicks": 200,
                "ctr": 2.0,
                "units_ordered": 20,
                "cvr": 10.0
            }
        }

        analysis = mye.determine_winner(metrics)

        assert analysis["winner"] == "CONTROL"
        assert analysis["ctr_lift_percent"] == -20.0  # 20% decline
        assert analysis["recommendation"] == "ROLLBACK"


class TestMYEExperimentRunner:
    """Test end-to-end experiment runner"""

    def test_experiment_blocked_by_lqs(self):
        """9. Test experiment blocked by low LQS"""
        runner = MYEExperimentRunner(headless=True)

        result = runner.run_experiment(
            asin="B01TEST",
            control_title="Old Title",
            treatment_title="Bad",  # Very short title will fail LQS
            duration_days=28
        )

        assert result["status"] == "BLOCKED"
        assert "LQS below MYE threshold" in result["reason"]

    @pytest.mark.skip(reason="Requires valid credentials and creates real experiment")
    def test_full_experiment_workflow(self):
        """10. Test complete experiment workflow"""
        runner = MYEExperimentRunner(headless=False)

        # Run experiment
        result = runner.run_experiment(
            asin="B01TEST",
            control_title="Old Product Title Here",
            treatment_title="Premium Wireless Headphones | Noise Cancelling | 40Hr Battery | Comfortable Design",
            duration_days=28
        )

        assert result["status"] == "RUNNING"
        assert "experiment_id" in result
        assert result["lqs_validation"]["eligible"] is True

        # Collect metrics
        experiment_id = result["experiment_id"]
        metrics_result = runner.collect_metrics(experiment_id)

        assert "metrics" in metrics_result
        assert "analysis" in metrics_result

        # Generate report
        report = runner.generate_report(experiment_id)

        assert "recommendation" in report
        assert report["asin"] == "B01TEST"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }
