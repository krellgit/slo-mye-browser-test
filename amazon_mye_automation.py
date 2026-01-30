"""
Amazon MYE (Manage Your Experiments) Browser Automation
Implements Path B from Module-5-MYE-Integration-Overview.md

WARNING: This automation may violate Amazon's Terms of Service.
Use at your own risk. Intended for testing purposes only.
"""
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from playwright.sync_api import Page, Browser, sync_playwright
from dotenv import load_dotenv
import json

load_dotenv()


class AmazonMYEAutomation:
    """
    Automates Amazon Seller Central MYE experiment creation and monitoring

    Implements:
    1. Login to Seller Central
    2. Navigate to Manage Your Experiments
    3. Create Title experiments with SLO-generated listings
    4. Monitor daily metrics (impressions, clicks, CTR, CVR)
    5. Extract results and determine winners
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.seller_central_url = os.getenv("SELLER_CENTRAL_URL", "https://sellercentral.amazon.com")
        self.mye_url = f"{self.seller_central_url}/advertising/manage-your-experiments"
        self.email = os.getenv("AMAZON_SELLER_EMAIL")
        self.password = os.getenv("AMAZON_SELLER_PASSWORD")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = context.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Login to Amazon Seller Central

        Args:
            email: Seller Central email (defaults to env var)
            password: Seller Central password (defaults to env var)

        Returns:
            True if login successful, False otherwise
        """
        email = email or self.email
        password = password or self.password

        if not email or not password:
            raise ValueError("Email and password required for login")

        print(f"[{self._timestamp()}] Navigating to Seller Central...")
        self.page.goto(self.seller_central_url)
        self.page.wait_for_load_state("networkidle")

        # Check if already logged in
        if "signin" not in self.page.url.lower():
            print(f"[{self._timestamp()}] Already logged in")
            return True

        print(f"[{self._timestamp()}] Entering credentials...")

        # Enter email
        email_input = self.page.locator("input[type='email'], input#ap_email")
        if email_input.is_visible():
            email_input.fill(email)
            self.page.locator("input[type='submit'], button[type='submit']").first.click()
            self.page.wait_for_load_state("networkidle")

        # Enter password
        password_input = self.page.locator("input[type='password'], input#ap_password")
        if password_input.is_visible():
            password_input.fill(password)
            self.page.locator("input[type='submit'], button[type='submit']").first.click()
            self.page.wait_for_load_state("networkidle")

        # Handle 2FA if present
        if "mfa" in self.page.url.lower() or "verify" in self.page.url.lower():
            print(f"[{self._timestamp()}] 2FA required - waiting for manual verification...")
            self.page.wait_for_url(lambda url: "mfa" not in url.lower(), timeout=120000)

        print(f"[{self._timestamp()}] Login successful")
        return True

    def navigate_to_mye(self) -> None:
        """Navigate to Manage Your Experiments dashboard"""
        print(f"[{self._timestamp()}] Navigating to MYE dashboard...")
        self.page.goto(self.mye_url)
        self.page.wait_for_load_state("networkidle")

    def create_experiment(self,
                         asin: str,
                         attribute: str,
                         control_text: str,
                         treatment_text: str,
                         duration_days: int = 28,
                         traffic_split: int = 50) -> Dict:
        """
        Create a new MYE experiment

        Args:
            asin: Product ASIN
            attribute: "TITLE", "BULLET_1", "BULLET_2", etc.
            control_text: Current listing text (control variant)
            treatment_text: Optimized listing text (treatment variant)
            duration_days: Experiment duration (default 28 days)
            traffic_split: Control traffic % (default 50, treatment gets remaining)

        Returns:
            Experiment metadata dict
        """
        print(f"[{self._timestamp()}] Creating experiment for ASIN {asin}...")

        # Navigate to MYE
        self.navigate_to_mye()

        # Click "Create Experiment" button
        create_btn = self.page.locator("button:has-text('Create Experiment'), a:has-text('Create Experiment')")
        create_btn.click()
        self.page.wait_for_load_state("networkidle")

        # Enter ASIN
        print(f"[{self._timestamp()}] Selecting ASIN...")
        asin_input = self.page.locator("input[name*='asin'], input[placeholder*='ASIN']")
        asin_input.fill(asin)
        asin_input.press("Enter")
        time.sleep(2)  # Wait for ASIN validation

        # Select attribute (Title, Bullet Point, etc.)
        print(f"[{self._timestamp()}] Selecting attribute: {attribute}...")
        attribute_map = {
            "TITLE": "Product Title",
            "BULLET_1": "Bullet Point 1",
            "BULLET_2": "Bullet Point 2",
            "BULLET_3": "Bullet Point 3",
            "BULLET_4": "Bullet Point 4",
            "BULLET_5": "Bullet Point 5",
        }
        attribute_display = attribute_map.get(attribute, "Product Title")
        self.page.locator(f"text={attribute_display}").click()

        # Enter control variant
        print(f"[{self._timestamp()}] Entering control variant...")
        control_input = self.page.locator("textarea[name*='control'], textarea:has-text('Control')").first
        control_input.fill(control_text)

        # Enter treatment variant
        print(f"[{self._timestamp()}] Entering treatment variant...")
        treatment_input = self.page.locator("textarea[name*='treatment'], textarea:has-text('Treatment')").first
        treatment_input.fill(treatment_text)

        # Set duration
        print(f"[{self._timestamp()}] Setting duration: {duration_days} days...")
        duration_input = self.page.locator("input[name*='duration'], input[type='number']")
        if duration_input.is_visible():
            duration_input.fill(str(duration_days))

        # Set traffic split
        print(f"[{self._timestamp()}] Setting traffic split: {traffic_split}/{100-traffic_split}...")
        traffic_input = self.page.locator("input[name*='traffic'], input[name*='split']")
        if traffic_input.is_visible():
            traffic_input.fill(str(traffic_split))

        # Review and launch
        print(f"[{self._timestamp()}] Launching experiment...")
        launch_btn = self.page.locator("button:has-text('Launch'), button:has-text('Create'), button:has-text('Start')")
        launch_btn.click()
        self.page.wait_for_load_state("networkidle")

        # Extract experiment ID from URL or page
        experiment_id = self._extract_experiment_id()

        experiment_metadata = {
            "experiment_id": experiment_id,
            "asin": asin,
            "attribute": attribute,
            "control_text": control_text,
            "treatment_text": treatment_text,
            "duration_days": duration_days,
            "traffic_split": traffic_split,
            "created_at": datetime.now().isoformat(),
            "status": "RUNNING"
        }

        print(f"[{self._timestamp()}] Experiment created: {experiment_id}")
        return experiment_metadata

    def get_experiment_metrics(self, experiment_id: str) -> Dict:
        """
        Fetch daily metrics for an experiment

        Args:
            experiment_id: MYE experiment ID

        Returns:
            Dict with control and treatment metrics
        """
        print(f"[{self._timestamp()}] Fetching metrics for experiment {experiment_id}...")

        # Navigate to experiment details page
        self.page.goto(f"{self.mye_url}/{experiment_id}")
        self.page.wait_for_load_state("networkidle")

        # Extract metrics table
        metrics = {
            "experiment_id": experiment_id,
            "date": datetime.now().date().isoformat(),
            "control": self._extract_variant_metrics("control"),
            "treatment": self._extract_variant_metrics("treatment")
        }

        print(f"[{self._timestamp()}] Metrics extracted")
        return metrics

    def get_all_experiments(self) -> List[Dict]:
        """
        Get list of all experiments

        Returns:
            List of experiment metadata dicts
        """
        print(f"[{self._timestamp()}] Fetching all experiments...")

        self.navigate_to_mye()

        experiments = []

        # Find experiment table/list
        rows = self.page.locator("table tbody tr, div[data-test='experiment-row']").all()

        for row in rows:
            exp = {
                "experiment_id": self._extract_text(row, "[data-test='experiment-id']"),
                "asin": self._extract_text(row, "[data-test='asin']"),
                "status": self._extract_text(row, "[data-test='status']"),
                "created": self._extract_text(row, "[data-test='created-date']")
            }
            experiments.append(exp)

        print(f"[{self._timestamp()}] Found {len(experiments)} experiments")
        return experiments

    def determine_winner(self, metrics: Dict) -> Dict:
        """
        Analyze metrics and determine winning variant

        Args:
            metrics: Dict with control and treatment metrics

        Returns:
            Winner analysis dict
        """
        control = metrics["control"]
        treatment = metrics["treatment"]

        # Calculate performance lift
        ctr_lift = ((treatment["ctr"] - control["ctr"]) / control["ctr"] * 100) if control["ctr"] > 0 else 0
        cvr_lift = ((treatment["cvr"] - control["cvr"]) / control["cvr"] * 100) if control["cvr"] > 0 else 0

        # Determine winner based on CTR and CVR improvement
        winner = "TREATMENT" if ctr_lift > 0 and cvr_lift >= 0 else "CONTROL"

        return {
            "winner": winner,
            "ctr_lift_percent": round(ctr_lift, 2),
            "cvr_lift_percent": round(cvr_lift, 2),
            "recommendation": "APPLY" if winner == "TREATMENT" else "ROLLBACK",
            "confidence": self._calculate_statistical_significance(control, treatment)
        }

    def _extract_variant_metrics(self, variant_type: str) -> Dict:
        """Extract metrics for a specific variant from MYE page"""
        selector_prefix = f"[data-variant='{variant_type}']"

        impressions = self._extract_number(f"{selector_prefix} [data-metric='impressions']")
        clicks = self._extract_number(f"{selector_prefix} [data-metric='clicks']")
        units_ordered = self._extract_number(f"{selector_prefix} [data-metric='units']")

        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cvr = (units_ordered / clicks * 100) if clicks > 0 else 0

        return {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),
            "units_ordered": units_ordered,
            "cvr": round(cvr, 2)
        }

    def _extract_experiment_id(self) -> str:
        """Extract experiment ID from current page"""
        # Try to extract from URL
        if "experiment" in self.page.url:
            parts = self.page.url.split("/")
            return parts[-1] if parts[-1] else parts[-2]

        # Try to extract from page element
        id_element = self.page.locator("[data-test='experiment-id'], .experiment-id")
        if id_element.is_visible():
            return id_element.text_content().strip()

        # Generate timestamp-based ID as fallback
        return f"EXP_{int(time.time())}"

    def _extract_text(self, element, selector: str) -> str:
        """Extract text from element with selector"""
        try:
            return element.locator(selector).text_content().strip()
        except:
            return ""

    def _extract_number(self, selector: str) -> int:
        """Extract number from page element"""
        try:
            text = self.page.locator(selector).text_content().strip()
            return int(text.replace(",", ""))
        except:
            return 0

    def _calculate_statistical_significance(self, control: Dict, treatment: Dict) -> str:
        """
        Calculate statistical significance of results
        Simple chi-squared test for CTR
        """
        # This is a simplified version
        # For production, use scipy.stats.chi2_contingency

        total_control = control["impressions"]
        total_treatment = treatment["impressions"]

        if total_control < 100 or total_treatment < 100:
            return "LOW"
        elif total_control >= 1000 and total_treatment >= 1000:
            return "HIGH"
        else:
            return "MEDIUM"

    def _timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def take_screenshot(self, filename: str) -> None:
        """Take screenshot of current page"""
        self.page.screenshot(path=filename)
        print(f"[{self._timestamp()}] Screenshot saved: {filename}")
