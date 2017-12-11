#!/usr/bin/env python3

from houseclown import test_events
import houseclown.lambda_function as func
from unittest.mock import patch
from unittest import TestCase, main
import json

class HouseClownTestCase(TestCase):

    maxDiff = None

    def common_test_structure(self, test_event):
        # Given
        event = test_event['event']
        expected_response = test_event['expected_response']

        # When
        generated_response = func.handler(event, None)

        # Then
        # General assertions
        self.assertEqual(generated_response, expected_response)


    # def test_clear(self, clear_mock):
    #     # parse test inputs
    #     test_event = test_events['Clear, good']
    #     # prepare mocks
    #     clear_mock.return_value = 'URLs cache cleared.'
    #
    #     # Run test
    #     self.common_test_structure(test_event)
    #
    #     # particular assertions
    #     clear_mock.assert_called()

if __name__ == '__main__':
    main(verbosity=2)
