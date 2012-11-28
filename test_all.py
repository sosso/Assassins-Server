import test_functional
import test_integration
import test_models
import unittest

models_suite = test_models.suite()
integration_suite = test_integration.suite()
functional_suite = test_functional.suite()
combined_suite = unittest.TestSuite([models_suite, integration_suite, functional_suite])
unittest.TextTestRunner(verbosity=2).run(combined_suite)