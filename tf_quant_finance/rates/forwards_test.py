# Lint as: python3
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for rate forwards."""

import numpy as np
import tensorflow.compat.v2 as tf
from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import
from tf_quant_finance.rates import forwards


@test_util.run_all_in_graph_and_eager_modes
class ForwardRatesTest(tf.test.TestCase):

  def test_forward_rates(self):
    dtypes = [np.float64, np.float32]
    for dtype in dtypes:
      groups = np.array([0, 0, 0, 1, 1, 1, 1])
      times = np.array([0.25, 0.5, 1.0, 0.25, 0.5, 1.0, 1.5], dtype=dtype)
      rates = np.array([0.04, 0.041, 0.044, 0.022, 0.025, 0.028, 0.036],
                       dtype=dtype)
      forward_rates = self.evaluate(
          forwards.forward_rates_from_yields(
              rates, times, groups=groups, dtype=dtype))
      expected_forward_rates = np.array(
          [0.04, 0.042, 0.047, 0.022, 0.028, 0.031, 0.052], dtype=dtype)
      np.testing.assert_allclose(
          forward_rates, expected_forward_rates, atol=1e-6)

  def test_forward_rates_no_batches(self):
    dtypes = [np.float64, np.float32]
    for dtype in dtypes:
      times = np.array([0.25, 0.5, 1.0, 1.25, 1.5, 2.0, 2.5], dtype=dtype)
      rates = np.array([0.04, 0.041, 0.044, 0.046, 0.046, 0.047, 0.050],
                       dtype=dtype)
      forward_rates = self.evaluate(
          forwards.forward_rates_from_yields(rates, times, dtype=dtype))
      expected_forward_rates = np.array(
          [0.04, 0.042, 0.047, 0.054, 0.046, 0.05, 0.062], dtype=dtype)
      np.testing.assert_allclose(
          forward_rates, expected_forward_rates, atol=1e-6)

  def test_yields_from_forwards(self):
    dtypes = [np.float64, np.float32]
    for dtype in dtypes:
      groups = np.array([0, 0, 0, 1, 1, 1, 1])
      times = np.array([0.25, 0.5, 1.0, 0.25, 0.5, 1.0, 1.5], dtype=dtype)
      forward_rates = np.array([0.04, 0.042, 0.047, 0.022, 0.028, 0.031, 0.052],
                               dtype=dtype)
      expected_rates = np.array(
          [0.04, 0.041, 0.044, 0.022, 0.025, 0.028, 0.036], dtype=dtype)
      actual_rates = self.evaluate(
          forwards.yields_from_forward_rates(
              forward_rates, times, groups=groups, dtype=dtype))
      np.testing.assert_allclose(actual_rates, expected_rates, atol=1e-6)

  def test_yields_from_forward_rates_no_batches(self):
    dtypes = [np.float64, np.float32]
    for dtype in dtypes:
      times = np.array([0.25, 0.5, 1.0, 1.25, 1.5, 2.0, 2.5], dtype=dtype)
      forward_rates = np.array([0.04, 0.042, 0.047, 0.054, 0.046, 0.05, 0.062],
                               dtype=dtype)
      expected_rates = np.array(
          [0.04, 0.041, 0.044, 0.046, 0.046, 0.047, 0.050], dtype=dtype)
      actual_rates = self.evaluate(
          forwards.yields_from_forward_rates(forward_rates, times, dtype=dtype))
      np.testing.assert_allclose(actual_rates, expected_rates, atol=1e-6)


if __name__ == '__main__':
  tf.test.main()
