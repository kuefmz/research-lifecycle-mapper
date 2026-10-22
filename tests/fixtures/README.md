# Historical regression fixtures

Legacy profiles and the previous packaged default are retained solely to test historical
matching and saved-format behavior. They are not supported alternatives to the final
105-rule method. Tests using legacy_catalog explicitly select these fixture rules;
production defaults are not monkeypatched. tests/test_submission.py checks the actual
final default against the unchanged scientific profile, including full evidence equality.
