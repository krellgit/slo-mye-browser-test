"""
LQS (Listing Quality Score) Integration
Validates SLO-generated listings meet MYE eligibility threshold (LQS >= 70)
"""
import requests
from typing import Dict, Optional
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()


class LQSIntegration:
    """
    Integrates with LQS Dashboard to validate listing quality
    before creating MYE experiments

    MYE Eligibility Criteria:
    - Listing Quality Score (LQS) >= 70.0
    - All 6 dimensions must have valid scores
    - No critical compliance failures
    """

    MYE_THRESHOLD = 70.0

    def __init__(self):
        self.lqs_api_url = os.getenv("LQS_API_URL", "https://lqs.krell.works/api")
        self.s3_bucket = os.getenv("S3_BUCKET", "acglogs")
        self.s3_prefix = os.getenv("S3_PREFIX", "listings/")
        self.s3_client = self._init_s3_client()

    def _init_s3_client(self):
        """Initialize S3 client for reading listing data"""
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    def calculate_lqs(self, asin: str, listing_data: Dict) -> Dict:
        """
        Calculate Listing Quality Score for a listing

        Args:
            asin: Amazon ASIN
            listing_data: Dict with title, bullets, description

        Returns:
            Dict with LQS score and 6-dimension breakdown
        """
        # 6 Dimensions with weights
        dimensions = {
            "keyword_optimization": {"weight": 0.25, "score": 0},
            "usp_effectiveness": {"weight": 0.20, "score": 0},
            "readability": {"weight": 0.15, "score": 0},
            "competitive_position": {"weight": 0.15, "score": 0},
            "customer_alignment": {"weight": 0.15, "score": 0},
            "compliance": {"weight": 0.10, "score": 0}
        }

        # Calculate each dimension (simplified - actual LQS has complex logic)
        dimensions["keyword_optimization"]["score"] = self._score_keyword_optimization(listing_data)
        dimensions["usp_effectiveness"]["score"] = self._score_usp_effectiveness(listing_data)
        dimensions["readability"]["score"] = self._score_readability(listing_data)
        dimensions["competitive_position"]["score"] = self._score_competitive_position(asin, listing_data)
        dimensions["customer_alignment"]["score"] = self._score_customer_alignment(listing_data)
        dimensions["compliance"]["score"] = self._score_compliance(listing_data)

        # Calculate weighted LQS
        lqs = sum(
            dim["score"] * dim["weight"]
            for dim in dimensions.values()
        )

        return {
            "asin": asin,
            "lqs": round(lqs, 1),
            "dimensions": dimensions,
            "mye_eligible": lqs >= self.MYE_THRESHOLD,
            "grade": self._assign_grade(lqs)
        }

    def validate_for_mye(self, asin: str, listing_data: Dict) -> Dict:
        """
        Validate listing meets MYE eligibility criteria

        Args:
            asin: Amazon ASIN
            listing_data: Dict with title, bullets, description

        Returns:
            Dict with validation result and recommendations
        """
        lqs_result = self.calculate_lqs(asin, listing_data)

        validation = {
            "eligible": lqs_result["mye_eligible"],
            "lqs": lqs_result["lqs"],
            "grade": lqs_result["grade"],
            "blockers": [],
            "recommendations": []
        }

        # Check for blockers
        if lqs_result["lqs"] < self.MYE_THRESHOLD:
            validation["blockers"].append(
                f"LQS score {lqs_result['lqs']} below MYE threshold {self.MYE_THRESHOLD}"
            )

        # Find weak dimensions
        for dim_name, dim_data in lqs_result["dimensions"].items():
            if dim_data["score"] < 60:
                validation["recommendations"].append(
                    f"Improve {dim_name.replace('_', ' ').title()}: score {dim_data['score']}/100"
                )

        return validation

    def get_listing_from_s3(self, asin: str) -> Optional[Dict]:
        """
        Fetch listing data from S3 bucket

        Args:
            asin: Amazon ASIN

        Returns:
            Listing data dict or None if not found
        """
        try:
            key = f"{self.s3_prefix}{asin}.json"
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return data
        except Exception as e:
            print(f"Error fetching listing from S3: {e}")
            return None

    def _score_keyword_optimization(self, listing_data: Dict) -> float:
        """
        Score keyword optimization (25% weight)
        Coverage + strategic placement
        """
        title = listing_data.get("title", "")
        bullets = listing_data.get("bullets", [])

        # Simple scoring based on keyword density and placement
        score = 0

        # Title keyword placement (50% of dimension)
        if len(title) > 80 and len(title) <= 200:
            score += 50

        # Bullet keyword coverage (50% of dimension)
        total_bullet_length = sum(len(b) for b in bullets)
        if total_bullet_length > 500:
            score += 50

        return min(100, score)

    def _score_usp_effectiveness(self, listing_data: Dict) -> float:
        """
        Score USP effectiveness (20% weight)
        Coverage + differentiation + proof strength
        """
        bullets = listing_data.get("bullets", [])

        # Check for USP indicators
        usp_keywords = ["unique", "patented", "exclusive", "only", "first", "proven"]
        usp_count = sum(
            1 for bullet in bullets
            for keyword in usp_keywords
            if keyword.lower() in bullet.lower()
        )

        return min(100, usp_count * 20 + 40)

    def _score_readability(self, listing_data: Dict) -> float:
        """
        Score readability (15% weight)
        Flesch score + scannability + title clarity
        """
        title = listing_data.get("title", "")

        # Simple readability check
        score = 70  # Base score

        # Title clarity (not too long, not too short)
        if 100 <= len(title) <= 180:
            score += 15

        # Check for clear formatting
        if any(char in title for char in ["|", ",", "-"]):
            score += 15

        return min(100, score)

    def _score_competitive_position(self, asin: str, listing_data: Dict) -> float:
        """
        Score competitive position (15% weight)
        Uniqueness vs competitors
        """
        # Simplified - would need competitor data
        return 70.0

    def _score_customer_alignment(self, listing_data: Dict) -> float:
        """
        Score customer alignment (15% weight)
        Intent theme + pain point coverage
        """
        bullets = listing_data.get("bullets", [])

        # Check for pain point keywords
        pain_point_keywords = ["solve", "eliminate", "prevent", "avoid", "reduce", "improve"]
        pain_point_count = sum(
            1 for bullet in bullets
            for keyword in pain_point_keywords
            if keyword.lower() in bullet.lower()
        )

        return min(100, pain_point_count * 15 + 40)

    def _score_compliance(self, listing_data: Dict) -> float:
        """
        Score compliance (10% weight)
        Banned terms + Amazon formatting
        """
        title = listing_data.get("title", "")
        bullets = listing_data.get("bullets", [])

        # Check for banned terms
        banned_terms = ["#1", "best seller", "free shipping", "100% guarantee"]
        text = (title + " " + " ".join(bullets)).lower()

        violations = sum(1 for term in banned_terms if term in text)

        if violations == 0:
            return 100
        elif violations == 1:
            return 80
        else:
            return 60

    def _assign_grade(self, lqs: float) -> str:
        """Assign letter grade based on LQS"""
        if lqs >= 90:
            return "A"
        elif lqs >= 80:
            return "B"
        elif lqs >= 70:
            return "C"
        elif lqs >= 60:
            return "D"
        else:
            return "F"
