"""Tests for the enterprise product tier licensing module."""

import unittest

from qkdpy.enterprise.licensing import (
    TIER_FEATURES,
    Feature,
    LicenseError,
    ProductTier,
    feature_available,
    get_active_tier,
    require_feature,
    set_active_tier,
)


class TestProductTierDefaults(unittest.TestCase):
    """Default tier is FREE."""

    def test_default_tier_is_free(self):
        """get_active_tier returns FREE by default."""
        self.assertEqual(get_active_tier(), ProductTier.FREE)

    def test_free_tier_has_no_compliance(self):
        """FREE tier does not have compliance features."""
        self.assertFalse(feature_available(Feature.COMPLIANCE_REPORTING))
        self.assertFalse(feature_available(Feature.COMPLIANCE_HTML_EXPORT))
        self.assertFalse(feature_available(Feature.ML_ATTACK_DETECTION))

    def test_free_tier_has_advanced_viz(self):
        """FREE tier has basic advanced visualisation."""
        self.assertTrue(feature_available(Feature.ADVANCED_VISUALIZATION))


class TestSetActiveTier(unittest.TestCase):
    """Setting the active tier enables the right features."""

    def setUp(self) -> None:
        self._orig_tier = get_active_tier()

    def tearDown(self) -> None:
        set_active_tier(self._orig_tier)

    def test_enterprise_enables_compliance(self):
        """ENTERPRISE tier enables compliance features."""
        set_active_tier(ProductTier.ENTERPRISE, license_key="demo-enterprise")
        self.assertTrue(feature_available(Feature.COMPLIANCE_REPORTING))
        self.assertTrue(feature_available(Feature.COMPLIANCE_HTML_EXPORT))
        self.assertTrue(feature_available(Feature.HSM_INTEGRATION))

    def test_enterprise_does_not_have_quantum_safe(self):
        """ENTERPRISE tier does not include quantum-safe features."""
        set_active_tier(ProductTier.ENTERPRISE, license_key="demo-enterprise")
        self.assertFalse(feature_available(Feature.QUANTUM_SAFE_MIGRATION))
        self.assertFalse(feature_available(Feature.CRYPTO_INVENTORY))

    def test_premium_has_all_features(self):
        """PREMIUM tier enables all features."""
        set_active_tier(ProductTier.PREMIUM, license_key="demo-premium")
        for feature in Feature:
            self.assertTrue(
                feature_available(feature),
                f"{feature.value} should be available in PREMIUM",
            )

    def test_non_free_tier_refuses_without_license(self):
        """A non-FREE tier must not silently activate without a license key."""
        with self.assertRaises(LicenseError):
            set_active_tier(ProductTier.ENTERPRISE)
        with self.assertRaises(LicenseError):
            set_active_tier(ProductTier.PREMIUM, license_key="")
        # Tier must remain FREE after the refused switch.
        self.assertEqual(get_active_tier(), ProductTier.FREE)

    def test_free_tier_does_not_require_license(self):
        """FREE tier activates without a license key."""
        set_active_tier(ProductTier.FREE)
        self.assertEqual(get_active_tier(), ProductTier.FREE)


class TestRequireFeatureDecorator(unittest.TestCase):
    """@require_feature raises LicenseError for unlicensed features."""

    def setUp(self) -> None:
        self._orig_tier = get_active_tier()
        set_active_tier(ProductTier.FREE)

    def tearDown(self) -> None:
        set_active_tier(self._orig_tier)

    def test_decorated_function_runs_when_feature_available(self):
        """@require_feature does not raise when feature is available."""
        set_active_tier(ProductTier.PREMIUM, license_key="demo-premium")

        @require_feature(Feature.QUANTUM_SAFE_MIGRATION)
        def do_migration() -> str:
            return "migrating"

        self.assertEqual(do_migration(), "migrating")

    def test_decorator_raises_for_unlicensed_feature(self):
        """@require_feature raises LicenseError on FREE tier."""

        @require_feature(Feature.COMPLIANCE_REPORTING)
        def do_compliance() -> str:
            return "compliance"

        with self.assertRaises(LicenseError):
            do_compliance()

    def test_decorator_error_message_mentions_tier(self):
        """LicenseError message includes the required tier name."""

        @require_feature(Feature.CRYPTO_INVENTORY)
        def scan() -> None:
            pass

        with self.assertRaises(LicenseError) as ctx:
            scan()
        self.assertIn("premium", str(ctx.exception).lower())

    def test_decorator_passes_args_through(self):
        """@require_feature does not interfere with function arguments."""
        set_active_tier(ProductTier.PREMIUM, license_key="demo-premium")

        @require_feature(Feature.ADVANCED_VISUALIZATION)
        def greet(name: str) -> str:
            return f"Hello {name}"

        self.assertEqual(greet("Alice"), "Hello Alice")


class TestFeatureAvailability(unittest.TestCase):
    """feature_available with explicit tier parameter."""

    def test_explicit_tier_overrides_active(self):
        """feature_available respects explicit tier parameter."""
        result = feature_available(
            Feature.COMPLIANCE_REPORTING, tier=ProductTier.ENTERPRISE
        )
        self.assertTrue(result)

    def test_explicit_free_tier(self):
        """feature_available with explicit FREE tier."""
        result = feature_available(Feature.COMPLIANCE_REPORTING, tier=ProductTier.FREE)
        self.assertFalse(result)


class TestTierFeaturesMap(unittest.TestCase):
    """TIER_FEATURES map is consistent."""

    def test_free_subset_of_enterprise(self):
        """Every FREE feature is also in ENTERPRISE."""
        for feat in TIER_FEATURES[ProductTier.FREE]:
            self.assertIn(feat, TIER_FEATURES[ProductTier.ENTERPRISE])

    def test_enterprise_subset_of_premium(self):
        """Every ENTERPRISE feature is also in PREMIUM."""
        for feat in TIER_FEATURES[ProductTier.ENTERPRISE]:
            self.assertIn(feat, TIER_FEATURES[ProductTier.PREMIUM])

    def test_all_features_covered(self):
        """Every Feature enum member appears in at least one tier."""
        covered: set[Feature] = set()
        for features in TIER_FEATURES.values():
            covered.update(features)
        for feat in Feature:
            self.assertIn(feat, covered, f"{feat.value} not in any tier")


if __name__ == "__main__":
    unittest.main()
