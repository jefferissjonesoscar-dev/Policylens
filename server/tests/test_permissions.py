"""
Tests for the Stage 7 app permissions explainer.
"""

import unittest

from app.errors import InputError
from app.permissions.explain import explain_permissions, find_permission_names


class FindPermissionNamesTests(unittest.TestCase):
    def test_reads_one_per_line_and_comma_separated(self):
        names = find_permission_names("android.permission.CAMERA, NSMicrophoneUsageDescription\nREAD_CONTACTS")
        self.assertEqual(names, [
            "android.permission.CAMERA",
            "NSMicrophoneUsageDescription",
            "android.permission.READ_CONTACTS",
        ])

    def test_reads_android_manifest_lines(self):
        manifest = """
        <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
        <uses-permission android:name="com.google.android.gms.permission.AD_ID"/>
        """
        self.assertEqual(find_permission_names(manifest), [
            "android.permission.ACCESS_FINE_LOCATION",
            "com.google.android.gms.permission.AD_ID",
        ])

    def test_ignores_ordinary_words_and_duplicates(self):
        names = find_permission_names("This app needs GPS and CAMERA. CAMERA again.")
        self.assertEqual(names, ["android.permission.CAMERA"])


class ExplainPermissionsTests(unittest.TestCase):
    def test_known_permissions_are_explained_most_sensitive_first(self):
        result = explain_permissions("VIBRATE\nCAMERA\nREAD_SMS\ncom.example.permission.CUSTOM")
        self.assertEqual([p["risk_level"] for p in result], ["High", "Medium", "Low", None])
        self.assertEqual(result[0]["title"], "Read your text messages")
        self.assertEqual(result[0]["platform"], "Android")
        self.assertEqual(result[-1]["title"], "Not in our list yet")

    def test_ios_keys_are_recognised(self):
        result = explain_permissions("NSUserTrackingUsageDescription")
        self.assertEqual((result[0]["platform"], result[0]["risk_level"]), ("iOS", "High"))

    def test_nothing_recognisable_is_an_error(self):
        with self.assertRaises(InputError) as caught:
            explain_permissions("hello world")
        self.assertEqual(caught.exception.code, "no_permissions_found")


if __name__ == "__main__":
    unittest.main()
