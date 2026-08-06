from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from departments.models import Department

from .categorization import _load_svm_model, categorize, categorizer_status
from .image_detection import detect_emergency


class CategorizationTests(SimpleTestCase):
    def test_packaged_svm_model_loads(self):
        _load_svm_model.cache_clear()
        self.assertEqual(categorizer_status()["engine"], "svm")

    def test_expected_civic_categories(self):
        examples = {
            "Deep pothole and cracked road": Department.Category.ROAD_DAMAGE,
            "A water pipe burst beside the school": Department.Category.WATER_LEAKAGE,
            "Overflowing garbage has not been collected": Department.Category.GARBAGE,
            "A transformer failed and caused a power outage": Department.Category.STREET_LIGHT,
            "Blocked drainage caused flooding": Department.Category.DRAINAGE,
            "An unrelated public-space concern": Department.Category.OTHERS,
        }
        for text, expected in examples.items():
            with self.subTest(text=text):
                self.assertEqual(categorize(text), expected)

    def test_valid_svm_prediction_takes_priority(self):
        class FakeModel:
            def predict(self, values):
                return ["Water Leakage"]

        with patch("ai_services.categorization._load_svm_model", return_value=FakeModel()):
            self.assertEqual(
                categorize("A generic issue without keyword signals"),
                Department.Category.WATER_LEAKAGE,
            )

    def test_unknown_svm_label_falls_back_safely(self):
        class FakeModel:
            def predict(self, values):
                return ["not-a-civicfix-category"]

        with patch("ai_services.categorization._load_svm_model", return_value=FakeModel()):
            self.assertEqual(categorize("Deep pothole"), Department.Category.ROAD_DAMAGE)


class EmergencyDetectionTests(SimpleTestCase):
    def test_explicit_danger_text_is_flagged_without_photo(self):
        result = detect_emergency(description="There is a fire and exposed wire")
        self.assertTrue(result.is_emergency)
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_normal_report_is_not_flagged_without_photo(self):
        result = detect_emergency(description="The bin has not been collected")
        self.assertFalse(result.is_emergency)


class LocationApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="location@example.com", password="StrongPassword!2026"
        )
        self.client.force_authenticate(self.user)

    @patch("ai_services.views.reverse_geocode", return_value="Pokhara, Nepal")
    def test_reverse_geocode_selected_location(self, mocked_reverse):
        response = self.client.get(
            "/api/location/reverse/?latitude=28.20960000&longitude=83.98560000"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["address"], "Pokhara, Nepal")
        mocked_reverse.assert_called_once_with(28.2096, 83.9856)

    def test_reverse_geocode_rejects_invalid_coordinates(self):
        response = self.client.get(
            "/api/location/reverse/?latitude=91&longitude=181"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
