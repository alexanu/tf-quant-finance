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
"""Tests for numeric integration methods."""

import collections
import math
import numpy as np
import tensorflow.compat.v2 as tf

import tf_quant_finance as tff
from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import

tff_int = tff.math.integration

IntegrationTestCase = collections.namedtuple('IntegrationTestCase', [
    'func',
    'lower',
    'upper',
    'antiderivative',
])

# pylint:disable=g-long-lambda
BASIC_TEST_CASES = [
    IntegrationTestCase(
        func=lambda x: tf.exp(2 * x + 1),
        lower=1.0,
        upper=3.0,
        antiderivative=lambda x: np.exp(2 * x + 1) / 2,
    ),
    IntegrationTestCase(
        func=lambda x: x**5,
        lower=-10.0,
        upper=100.0,
        antiderivative=lambda x: x**6 / 6,
    ),
    IntegrationTestCase(
        func=lambda x: (x**3 + x**2 - 4 * x + 1) / (x**2 + 1)**2,
        lower=0.0,
        upper=10.0,
        antiderivative=lambda x: sum([
            2.5 / (x**2 + 1),
            0.5 * np.log(x**2 + 1),
            np.arctan(x),
        ]),
    ),
    IntegrationTestCase(
        func=lambda x: (tf.sinh(2 * x) + 3 * tf.sinh(x)) /
        (tf.cosh(x)**2 + 2 * tf.cosh(0.5 * x)**2),
        lower=2.0,
        upper=4.0,
        antiderivative=lambda x: sum([
            np.log(np.cosh(x)**2 + np.cosh(x) + 1),
            (4 / np.sqrt(3)) * np.arctan((1 + 2 * np.cosh(x)) / np.sqrt(3.0)),
        ]),
    ),
    IntegrationTestCase(
        func=lambda x: tf.exp(2 * x) * tf.math.sqrt(tf.exp(x) + tf.exp(2 * x)),
        lower=2.0,
        upper=4.0,
        antiderivative=lambda x: sum([
            np.sqrt((np.exp(x) + np.exp(2 * x))**3) / 3,
            -(1 + 2 * np.exp(x)) * np.sqrt(np.exp(x) + np.exp(2 * x)) / 8,
            np.log(np.sqrt(1 + np.exp(x)) + np.exp(0.5 * x)) / 8,
        ]),
    ),
    IntegrationTestCase(
        func=lambda x: tf.exp(-x**2),
        lower=0.0,
        upper=1.0,
        antiderivative=lambda x: 0.5 * np.sqrt(np.pi) * math.erf(x),
    ),
]

TEST_CASE_RAPID_CHANGE = IntegrationTestCase(
    func=lambda x: 1.0 / tf.sqrt(x + 1e-6),
    lower=0.0,
    upper=1.0,
    antiderivative=lambda x: 2.0 * np.sqrt(x + 1e-6),
)


class IntegrationTest(tf.test.TestCase):

  def _test_batches_and_types(self, integrate_function, args):
    """Checks handling batches and dtypes."""
    dtypes = [np.float32, np.float64, np.complex64, np.complex128]
    a = [[0.0, 0.0], [0.0, 0.0]]
    b = [[np.pi / 2, np.pi], [1.5 * np.pi, 2 * np.pi]]
    a = [a, a]
    b = [b, b]
    k = tf.constant([[[[1.0]]], [[[2.0]]]])
    func = lambda x: tf.cast(k, dtype=x.dtype) * tf.sin(x)
    ans = [[[1.0, 2.0], [1.0, 0.0]], [[2.0, 4.0], [2.0, 0.0]]]

    results = []
    for dtype in dtypes:
      lower = tf.constant(a, dtype=dtype)
      upper = tf.constant(b, dtype=dtype)
      results.append(integrate_function(func, lower, upper, **args))

    results = self.evaluate(results)

    for i in range(len(results)):
      assert results[i].dtype == dtypes[i]
      assert np.allclose(results[i], ans, atol=1e-3)

  def _test_accuracy(self, integrate_function, args, test_case, max_rel_error):
    func = test_case.func
    lower = tf.constant(test_case.lower, dtype=tf.float64)
    upper = tf.constant(test_case.upper, dtype=tf.float64)
    exact = test_case.antiderivative(
        test_case.upper) - test_case.antiderivative(test_case.lower)
    approx = integrate_function(func, lower, upper, **args)
    approx = self.evaluate(approx)
    assert np.abs(approx - exact) <= np.abs(exact) * max_rel_error

  def _test_gradient(self, integrate_function, args):
    """Checks that integration result can be differentiated."""

    # We consider I(a) = int_0^1 cos(ax) dx.
    # Then dI/da = (a*cos(a) - sin(a))/a^2.
    def integral(a):
      return integrate_function(
          lambda x: tf.cos(a * x), 0.0, 1.0, dtype=tf.float64, **args)

    a = tf.constant(0.5, dtype=tf.float64)
    di_da = tff.math.fwd_gradient(integral, a)

    true_di_da = lambda a: (a * np.cos(a) - np.sin(a)) / (a**2)
    self.assertAllClose(self.evaluate(di_da), true_di_da(0.5))

  def test_integrate_batches_and_types(self):
    self._test_batches_and_types(tff_int.integrate, {})
    for method in tff_int.IntegrationMethod:
      self._test_batches_and_types(tff_int.integrate, {'method': method})

  def test_integrate_accuracy(self):
    for test_case in BASIC_TEST_CASES:
      self._test_accuracy(tff_int.integrate, {}, test_case, 1e-8)
      for method in tff_int.IntegrationMethod:
        self._test_accuracy(tff_int.integrate, {'method': method}, test_case,
                            1e-8)

  def test_integrate_gradient(self):
    for method in tff_int.IntegrationMethod:
      self._test_gradient(tff_int.integrate, {'method': method})

  def test_integrate_int_limits(self):
    for method in tff_int.IntegrationMethod:
      result = tff_int.integrate(tf.sin, 0, 1, method=method, dtype=tf.float64)
      result = self.evaluate(result)
      self.assertAllClose(0.459697694, result)

  def test_simpson_batches_and_types(self):
    self._test_batches_and_types(tff_int.simpson, {})

  def test_simpson_accuracy(self):
    for test_case in BASIC_TEST_CASES:
      self._test_accuracy(tff_int.simpson, {}, test_case, 1e-8)

  def test_simpson_rapid_change(self):
    self._test_accuracy(tff_int.simpson, {'num_points': 1001},
                        TEST_CASE_RAPID_CHANGE, 2e-1)
    self._test_accuracy(tff_int.simpson, {'num_points': 10001},
                        TEST_CASE_RAPID_CHANGE, 3e-2)
    self._test_accuracy(tff_int.simpson, {'num_points': 100001},
                        TEST_CASE_RAPID_CHANGE, 5e-4)
    self._test_accuracy(tff_int.simpson, {'num_points': 1000001},
                        TEST_CASE_RAPID_CHANGE, 3e-6)

  def test_simpson_gradient(self):
    self._test_gradient(tff_int.simpson, {})


if __name__ == '__main__':
  tf.test.main()
