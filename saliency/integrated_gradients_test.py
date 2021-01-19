# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import numpy as np
import tensorflow.compat.v1 as tf
from . import integrated_gradients
from tensorflow import test


class IntegratedGradientsTest(test.TestCase):
  """
  To run:
  "python -m saliency.integrated_gradients_test" from the PAIR-code/saliency
  directory.
  """

  def testIntegratedGradientsGetMask(self):
    
    def create_call_model_function(session, grad_node, x):
      def call_model(x_value, call_model_args={}, expected_keys=None):
        call_model_args[x] = [x_value]
        data = session.run(grad_node, feed_dict=call_model_args)
        return {'output_gradients' : data[0]}
      return call_model

    with tf.Graph().as_default() as graph:
      x = tf.placeholder(shape=[None, 3], dtype=tf.float32)
      y = 5 * x[:, 0] + x[:, 0] * x[:, 1] + tf.sin(x[:, 2])
      gradients_node = tf.gradients(y, x)[0]
      sess = tf.Session(graph=graph)

      # Calculate the value of `y` at the baseline.
      x_baseline_val = np.array([[0.5, 0.8, 1.0]], dtype=np.float)
      y_baseline_val = sess.run(y, feed_dict={x: x_baseline_val})

      # Calculate the value of `y` at the input.
      x_input_val = np.array([[1.0, 2.0, 3.0]], dtype=np.float)
      y_input_val = sess.run(y, feed_dict={x: x_input_val})

      # Due to mathematical properties of the integrated gradients,
      # the expected IG value is equal to the difference between
      # the `y` value at the input and the `y` value at the baseline.
      expected_val = y_input_val[0] - y_baseline_val[0]

      # Create a call_model_function using sess and tensors.
      call_model_function = create_call_model_function(sess, gradients_node, x)

      # Calculate the integrated gradients attribution of the input.
      ig = integrated_gradients.IntegratedGradients()
      mask = ig.GetMask(x_value=x_input_val[0], 
                        call_model_function=call_model_function,
                        call_model_args={},
                        x_baseline=x_baseline_val[0], 
                        x_steps=1000)

      # Verify the result.
      self.assertAlmostEqual(expected_val, mask.sum(), places=3)


if __name__ == '__main__':
  test.main()
