# SLO MYE Browser Automation Checkpoints

## SLOMYE-001 - 2026-01-30T20:08:00Z

**Summary:** Built Amazon MYE browser automation with LQS validation

**Goal:** Create browser automation to test SLO-generated listings on Amazon's Manage Your Experiments (MYE) platform, with LQS validation to ensure only high-quality listings (>= 70 threshold) are tested.

**Status:** Complete

**Changes:**
1. Created complete browser automation framework for Amazon Seller Central
2. Implemented 6-dimension LQS validation system
3. Built end-to-end experiment runner orchestrating full workflow
4. Added comprehensive test suite with 10 test cases
5. Created example usage scripts demonstrating 6 workflows
6. Integrated with S3 bucket for SLO-generated listing data
7. Implemented winner determination with statistical analysis
8. Added experiment lifecycle management and reporting

**Files modified:**
1. amazon_mye_automation.py (new)
2. lqs_integration.py (new)
3. mye_experiment_runner.py (new)
4. test_mye_automation.py (new)
5. example_usage.py (new)
6. requirements.txt (new)
7. pytest.ini (new)
8. README.md (new)
9. .env.example (new)
10. .gitignore (new)

**Commits:**
1. e5ec8cc - Complete rebuild: Amazon MYE browser automation
2. b0c3dc8 - Add comprehensive example usage scripts

**Key decisions:**
1. **Implemented Path B (Browser Automation)** from Module 5 MYE specification despite TOS risks
   - Rationale: User specifically requested browser automation, no other options acceptable
   - Trade-off: Full automation vs. potential Amazon TOS violation
   - Alternative rejected: Path A (Manual Hybrid) was not considered per user requirement

2. **Used Playwright over Selenium**
   - Rationale: Modern, faster, better debugging tools, cleaner API
   - Trade-off: Smaller ecosystem vs. better performance
   - Playwright's codegen feature makes selector discovery easier

3. **Enforced LQS >= 70 threshold before experiment creation**
   - Rationale: MYE eligibility criteria from LQS Dashboard spec
   - Prevents wasting experiment slots on low-quality listings
   - Grade C or better required (A/B/C pass, D/F blocked)

4. **Placeholder selectors instead of real Seller Central selectors**
   - Rationale: No access to actual Amazon Seller Central UI
   - User needs to use Playwright codegen to capture real selectors
   - Framework structure and logic are production-ready, only selectors need updating

5. **Sequential testing (Title first, then bullets)**
   - Rationale: Clean attribution - can't determine which change caused lift if testing multiple attributes
   - Follows Module 5 spec recommendation
   - Retest queue blocks progression until current attribute passes

6. **Winner determination based on CTR + CVR lift**
   - Rationale: Treatment wins if CTR improves AND CVR doesn't decline
   - Simple statistical significance (sample size based)
   - Production version should use chi-squared test (scipy.stats)

7. **28-day default duration with 50/50 traffic split**
   - Rationale: Amazon's recommended settings for statistical significance
   - Configurable but defaults to best practices

8. **Transparent documentation of TOS risks**
   - Rationale: Ethical responsibility to warn about account suspension risk
   - README includes prominent warnings and disclaimers
   - Suggests Path A as safer alternative

**Blockers:** None

**Next steps:**
1. User must add Amazon Seller Central credentials to .env file
2. Use Playwright codegen to capture real Seller Central selectors:
   ```bash
   playwright codegen sellercentral.amazon.com
   ```
3. Replace placeholder selectors in amazon_mye_automation.py with real ones
4. Test on development/staging account first to avoid production account suspension
5. Consider implementing Path C (Future API Integration) when Amazon releases MYE API
6. Add more sophisticated statistical significance testing (chi-squared)
7. Implement screenshot OCR for metrics extraction as fallback
8. Consider building hybrid mode that generates export PDFs (Path A fallback)

---
