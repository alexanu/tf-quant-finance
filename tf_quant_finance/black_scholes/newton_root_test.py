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


"""Tests for the Newton root finder in implied_vol_newton.py."""


from absl.testing import parameterized

import numpy as np
import tensorflow.compat.v2 as tf

from tf_quant_finance.black_scholes import implied_vol_newton_root as ivn

from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import


@test_util.run_all_in_graph_and_eager_modes
class NewtonRootTest(parameterized.TestCase, tf.test.TestCase):
  """Tests for the Newton root finder."""

  def test_newton_root_finder(self):
    """Tests that the newton root finder works on a square root example."""

    # Set up the problem of finding the square roots of three numbers.
    constants = np.array([4.0, 9.0, 16.0])
    initial_values = np.ones(len(constants))

    def objective_and_gradient(values):
      objective = values**2 - constants
      gradient = 2.0 * values
      return objective, gradient

    # Obtain and evaluate a tensor containing the roots.
    roots = ivn.newton_root_finder(objective_and_gradient, initial_values)
    root_values, converged, failed = self.evaluate(roots)

    # Reference values.
    roots_bench = np.array([2.0, 3.0, 4.0])
    converged_bench = np.array([True, True, True])
    failed_bench = np.array([False, False, False])

    # Assert that the values we obtained are close to the true values.
    np.testing.assert_array_equal(converged, converged_bench)
    np.testing.assert_array_equal(failed, failed_bench)
    np.testing.assert_almost_equal(root_values, roots_bench, decimal=7)

  def test_failure_and_non_convergence(self):
    """Tests that we can determine when the root finder has failed."""

    # Set up the problem of finding the square roots of three numbers.
    constants = np.array([4.0, 9.0, 16.0])
    # Choose a bad initial position.
    initial_values = np.zeros(len(constants))

    def objective_and_gradient(values):
      objective = values**2 - constants
      gradient = 2.0 * values
      return objective, gradient

    # Obtain and evaluate a tensor containing the roots.
    roots = ivn.newton_root_finder(objective_and_gradient, initial_values)
    _, converged, failed = self.evaluate(roots)

    # Reference values - we should not have converged and should have failed.
    converged_bench = np.array([False, False, False])
    failed_bench = np.array([True, True, True])

    # Assert that the values we obtained are close to the true values.
    np.testing.assert_array_equal(converged, converged_bench)
    np.testing.assert_array_equal(failed, failed_bench)

  def test_too_low_max_iterations(self):
    """Tests that we can determine when max_iterations was too small."""

    # Set up the problem of finding the square roots of three numbers.
    constants = np.array([4.0, 9.0, 16.0])
    initial_values = np.ones(len(constants))

    def objective_and_gradient(values):
      objective = values**2 - constants
      gradient = 2.0 * values
      return objective, gradient

    # Obtain and evaluate a tensor containing the roots.
    roots = ivn.newton_root_finder(
        objective_and_gradient, initial_values, max_iterations=1)
    _, converged, failed = self.evaluate(roots)

    # Reference values - we should neither have converged nor failed.
    converged_bench = np.array([False, False, False])
    failed_bench = np.array([False, False, False])

    # Assert that the values we obtained are close to the true values.
    np.testing.assert_array_equal(converged, converged_bench)
    np.testing.assert_array_equal(failed, failed_bench)


if __name__ == '__main__':
  tf.test.main()
