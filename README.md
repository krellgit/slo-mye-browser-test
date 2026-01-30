# SLO MYE Browser Automation

Browser automation for testing SLO-generated listings on Amazon's Manage Your Experiments (MYE) platform.

**⚠️ WARNING: This implements Path B (Browser Automation) from Module 5 MYE specification, which may violate Amazon's Terms of Service. Use at your own risk. Intended for testing and development purposes only.**

## Purpose

1. Automate Amazon Seller Central for MYE experiment creation
2. Validate SLO-generated listings with LQS before testing (>= 70 threshold)
3. Create Title experiments with optimized listings
4. Monitor experiment metrics (impressions, clicks, CTR, CVR)
5. Determine winners and generate reports

## Architecture

### 1. Components

1.1. **LQS Integration** (`lqs_integration.py`)
1.1.1. Calculates Listing Quality Score (6 dimensions)
1.1.2. Validates MYE eligibility (LQS >= 70)
1.1.3. Provides recommendations for improvement
1.1.4. Integrates with S3 listing data

1.2. **Amazon MYE Automation** (`amazon_mye_automation.py`)
1.2.1. Seller Central login automation
1.2.2. MYE experiment creation
1.2.3. Metrics collection (daily performance data)
1.2.4. Winner determination (statistical analysis)

1.3. **Experiment Runner** (`mye_experiment_runner.py`)
1.3.1. End-to-end workflow orchestration
1.3.2. Experiment lifecycle management
1.3.3. Report generation
1.3.4. Data persistence

### 2. Technology Stack

2.1. **Playwright**: Browser automation engine
2.2. **Python 3.10+**: Core language
2.3. **Boto3**: AWS S3 integration for listing data
2.4. **Pytest**: Test framework

### 3. Integration Points

3.1. **LQS Dashboard** (https://lqs.krell.works)
3.1.1. Validates listing quality before MYE testing
3.1.2. 6-dimension scoring framework
3.1.3. MYE eligibility determination

3.2. **Amazon Seller Central**
3.2.1. Automated login
3.2.2. Navigate to Manage Your Experiments
3.2.3. Create Title experiments
3.2.4. Extract performance metrics

3.3. **S3 Bucket** (acglogs/listings/)
3.3.1. Source for SLO-generated listing data
3.3.2. JSON format with title, bullets, description

## Setup

### 1. Prerequisites

1.1. Python 3.10 or higher
1.2. Amazon Seller Central account with MYE access
1.3. Professional Seller Plan (required for MYE)
1.4. AWS credentials (for S3 listing data access)

### 2. Installation

```bash
# 2.1. Clone repository
git clone https://github.com/krellgit/slo-mye-browser-test.git
cd slo-mye-browser-test

# 2.2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2.3. Install dependencies
pip install -r requirements.txt

# 2.4. Install Playwright browsers
playwright install chromium
```

### 3. Configuration

3.1. Copy `.env.example` to `.env`
3.2. Add Amazon Seller Central credentials
3.3. Configure AWS credentials for S3 access
3.4. Set LQS API URL (default: https://lqs.krell.works)

```bash
cp .env.example .env
# Edit .env with your credentials
```

**⚠️ CRITICAL: Never commit .env file to git - contains sensitive credentials**

## Usage

### 1. Quick Start Example

```python
from mye_experiment_runner import MYEExperimentRunner

# 1.1. Initialize runner
runner = MYEExperimentRunner(headless=False)

# 1.2. Run experiment
result = runner.run_experiment(
    asin="B01EXAMPLE",
    control_title="Old Product Title",
    treatment_title="Optimized Title | Key Benefits | Brand Name",
    duration_days=28
)

# 1.3. Check result
if result["status"] == "RUNNING":
    experiment_id = result["experiment_id"]
    print(f"Experiment {experiment_id} created!")
elif result["status"] == "BLOCKED":
    print(f"Blocked: {result['reason']}")
    print("LQS Score:", result["lqs_validation"]["lqs"])
```

### 2. Workflow Steps

2.1. **LQS Validation**
2.1.1. Treatment listing evaluated against 6 dimensions
2.1.2. Must score >= 70 for MYE eligibility
2.1.3. Blocked if criteria not met

2.2. **Experiment Creation**
2.2.1. Automated Seller Central login
2.2.2. Navigate to MYE dashboard
2.2.3. Create Title experiment
2.2.4. Control vs Treatment (50/50 traffic split)
2.2.5. 28-day duration (default)

2.3. **Metrics Collection**
```python
# Collect daily metrics
metrics_result = runner.collect_metrics(experiment_id)

print("Control CTR:", metrics_result["metrics"]["control"]["ctr"])
print("Treatment CTR:", metrics_result["metrics"]["treatment"]["ctr"])
print("Winner:", metrics_result["analysis"]["winner"])
```

2.4. **Report Generation**
```python
# Generate comprehensive report
report = runner.generate_report(experiment_id)

print("Recommendation:", report["recommendation"])
print("LQS Score:", report["lqs_score"])
print("CTR Lift:", report["analysis"]["ctr_lift_percent"], "%")
```

### 3. Testing

3.1. **Run all tests**
```bash
pytest
```

3.2. **Run LQS tests only**
```bash
pytest -m lqs
```

3.3. **Run with visible browser**
```bash
pytest --headed
```

3.4. **Skip integration tests** (don't require credentials)
```bash
pytest -m "not integration"
```

## LQS Validation

### 1. Six Dimensions

1.1. **Keyword Optimization** (25% weight)
1.1.1. Keyword coverage and density
1.1.2. Strategic placement in title
1.1.3. Character count optimization

1.2. **USP Effectiveness** (20% weight)
1.2.1. Unique selling proposition coverage
1.2.2. Differentiation strength
1.2.3. Proof elements (patented, exclusive, etc.)

1.3. **Readability** (15% weight)
1.3.1. Flesch reading score
1.3.2. Title clarity and structure
1.3.3. Scannability

1.4. **Competitive Position** (15% weight)
1.4.1. Uniqueness vs competitors
1.4.2. Market differentiation

1.5. **Customer Alignment** (15% weight)
1.5.1. Pain point coverage
1.5.2. Customer intent matching

1.6. **Compliance** (10% weight)
1.6.1. No banned terms
1.6.2. Amazon formatting guidelines

### 2. MYE Eligibility Criteria

2.1. Listing Quality Score >= 70.0
2.2. All 6 dimensions have valid scores
2.3. No critical compliance failures
2.4. Grade of C or better (A/B/C pass, D/F fail)

### 3. Grade Scale

3.1. **A Grade**: 90-100 (Excellent)
3.2. **B Grade**: 80-89 (Good)
3.3. **C Grade**: 70-79 (Acceptable, MYE eligible)
3.4. **D Grade**: 60-69 (Needs improvement)
3.5. **F Grade**: 0-59 (Poor, MYE ineligible)

## MYE Experiment Details

### 1. Experiment Settings

1.1. **Attribute**: TITLE (testing Title only, bullets tested separately)
1.2. **Duration**: 28 days (Amazon recommended)
1.3. **Traffic Split**: 50% Control / 50% Treatment
1.4. **Sequential Testing**: One attribute at a time

### 2. Metrics Collected

2.1. **Impressions**: Number of times product shown
2.2. **Clicks**: Number of clicks on product
2.3. **CTR**: Click-through rate (Clicks / Impressions * 100)
2.4. **Units Ordered**: Number of units purchased
2.5. **CVR**: Conversion rate (Units / Clicks * 100)

### 3. Winner Determination

3.1. **Treatment Wins** if:
3.1.1. CTR improvement > 0%
3.1.2. CVR improvement >= 0%
3.1.3. Statistical significance achieved

3.2. **Control Wins** if:
3.2.1. Treatment underperforms on CTR or CVR
3.2.2. Recommendation: ROLLBACK

3.3. **Retest** if:
3.3.1. No clear winner
3.3.2. Insufficient data
3.3.3. Recommendation: RETEST with adjusted variant

## File Structure

```
slo-mye-browser-test/
├── amazon_mye_automation.py    # Seller Central automation
├── lqs_integration.py          # LQS validation logic
├── mye_experiment_runner.py   # End-to-end orchestrator
├── test_mye_automation.py     # Test suite
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
└── experiments/              # Experiment data (gitignored)
    ├── EXP_123.json          # Experiment metadata
    └── EXP_123_report.json   # Generated reports
```

## Risks and Limitations

### 1. Terms of Service

1.1. **Amazon TOS Risk**: Browser automation may violate Amazon Seller Central Terms of Service
1.2. **Account Suspension**: Amazon may suspend seller accounts using automation
1.3. **Detection**: Amazon uses CAPTCHA and bot detection
1.4. **Recommendation**: Use at your own risk, consider Manual Hybrid approach (Path A)

### 2. Technical Limitations

2.1. **UI Changes**: Breaks when Amazon updates Seller Central UI
2.2. **CAPTCHA**: May block automation attempts
2.3. **2FA**: Requires manual intervention for two-factor authentication
2.4. **Rate Limits**: Amazon may rate-limit automated requests

### 3. Maintenance

3.1. Regular updates needed for Seller Central UI changes
3.2. Selector updates when Amazon changes HTML structure
3.3. Error handling for edge cases
3.4. Testing on staging/development accounts recommended

## Migration Path

### 1. Current Implementation (Path B)

1.1. Browser automation via Playwright
1.2. Manual intervention for 2FA
1.3. Fragile to UI changes

### 2. Future API Integration (Path C)

2.1. When Amazon releases MYE API
2.2. Swap to API adapter implementation
2.3. No upstream module changes needed
2.4. Abstraction layer already in place

### 3. Fallback to Manual Hybrid (Path A)

3.1. Generate export packages (PDF)
3.2. User creates experiments manually
3.3. User enters metrics via web form
3.4. Compliant and TOS-safe

## Related Projects

1. **LQS Dashboard**: Listing Quality Score calculator (https://lqs.krell.works)
2. **SLO**: Main SaaS Listing Optimization platform
3. **SLORO**: SLO rollout orchestrator
4. **SLOVD**: SLO Verification Dashboard

## References

1. **Module 5 Specification**: `/saas-listing-optimization/Listing Optimization Artifacts/markdown/Module-5-MYE-Integration-Overview.md`
2. **LQS Specification**: Lines 1-71 in LQS README
3. **Amazon MYE Documentation**: Seller Central > Advertising > Manage Your Experiments

## Support

### 1. Issues

1.1. Login failures: Check credentials in .env
1.2. CAPTCHA blocking: Run in headed mode, solve manually
1.3. UI selector errors: Amazon updated UI, selectors need update
1.4. LQS failures: Improve listing quality, check recommendations

### 2. Debugging

2.1. Run with `headless=False` to watch automation
2.2. Screenshots saved on errors
2.3. Playwright traces available for analysis
2.4. Check experiment JSON files for data

### 3. Best Practices

3.1. Test on development/staging accounts first
3.2. Start with headless=False to verify flow
3.3. Monitor for Amazon TOS violations
3.4. Keep credentials secure
3.5. Regular backups of experiment data

## Disclaimer

This tool automates Amazon Seller Central, which may violate Amazon's Terms of Service. Use at your own risk. The authors are not responsible for account suspensions, data loss, or any other consequences of using this automation tool.

For production use, consider the Manual Hybrid approach (Path A) from the Module 5 specification, which is TOS-compliant and lower risk.

## License

MIT

## Author

Built for SaaS Listing Optimization Platform by krellgit
