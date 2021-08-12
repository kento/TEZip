import os
import numpy as np
import hickle as hkl
np.random.seed(123)
from six.moves import cPickle

from keras import backend as K
from keras.models import Model
from keras.layers import Input, Dense, Flatten
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.callbacks import LearningRateScheduler, ModelCheckpoint
from keras.optimizers import Adam

from prednet import PredNet
from data_utils import SequenceGenerator

def run(WEIGHTS_DIR, DATA_DIR, VERBOSE):
  save_model = True  # if weights will be saved
  weights_file = os.path.join(WEIGHTS_DIR, 'prednet_weights.hdf5')  # where weights will be saved
  json_file = os.path.join(WEIGHTS_DIR, 'prednet_model.json')

  # Data files
  train_file = os.path.join(DATA_DIR, 'X_train.hkl')
  train_sources = os.path.join(DATA_DIR, 'sources_train.hkl')
  val_file = os.path.join(DATA_DIR, 'X_val.hkl')
  val_sources = os.path.join(DATA_DIR, 'sources_val.hkl')
  try:
      image_shape = hkl.load(train_file)
  except ValueError as e:
      print("ERROR: No such file or directory:", train_file)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()
  except OSError as e:
      print("ERROR: No such file or directory:", train_file)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()
  # Training parameters
  nb_epoch = 100
  batch_size = 1
  samples_per_epoch = 5
  N_seq_val = 2  # number of sequences to use for validation

  # Model parameters
  n_channels, im_height, im_width = (3, image_shape.shape[1], image_shape.shape[2])
  input_shape = (n_channels, im_height, im_width) if K.image_data_format() == 'channels_first' else (im_height, im_width, n_channels)
  stack_sizes = (n_channels, 48, 96, 192)
  R_stack_sizes = stack_sizes
  A_filt_sizes = (3, 3, 3)
  Ahat_filt_sizes = (3, 3, 3, 3)
  R_filt_sizes = (3, 3, 3, 3)
  layer_loss_weights = np.array([1., 0., 0., 0.])  # weighting for each layer in final loss; "L_0" model:  [1, 0, 0, 0], "L_all": [1, 0.1, 0.1, 0.1]
  layer_loss_weights = np.expand_dims(layer_loss_weights, 1)
  nt = 2  # number of timesteps used for sequences in training
  time_loss_weights = 1./ (nt - 1) * np.ones((nt,1))  # equally weight all timesteps except the first
  time_loss_weights[0] = 0


  prednet = PredNet(stack_sizes, R_stack_sizes,
                    A_filt_sizes, Ahat_filt_sizes, R_filt_sizes,
                    output_mode='error', return_sequences=True)

  inputs = Input(shape=(nt,) + input_shape)
  errors = prednet(inputs)  # errors will be (batch_size, nt, nb_layers)
  errors_by_time = TimeDistributed(Dense(1, trainable=False), weights=[layer_loss_weights, np.zeros(1)], trainable=False)(errors)  # calculate weighted error by layer
  errors_by_time = Flatten()(errors_by_time)  # will be (batch_size, nt)
  final_errors = Dense(1, weights=[time_loss_weights, np.zeros(1)], trainable=False)(errors_by_time)  # weight errors by time
  model = Model(inputs=inputs, outputs=final_errors)
  model.compile(loss='mean_absolute_error', optimizer='adam')
  
  try:
      train_generator = SequenceGenerator(train_file, train_sources, nt, batch_size=batch_size, shuffle=True)
  except ValueError as e:
      print("ERROR: No such file or directory:", train_file, " or ", train_sources)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()
  except OSError as e:
      print("ERROR: No such file or directory:", train_file, " or ", train_sources)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()

  try:
      val_generator = SequenceGenerator(val_file, val_sources, nt, batch_size=batch_size, N_seq=N_seq_val)
  except ValueError as e:
      print("ERROR: No such file or directory:", val_file, " or ", val_sources)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()
  except OSError as e:
      print("ERROR: No such file or directory:", val_file, " or ", val_sources)
      print("or")
      print("ERROR: There is not enough memory to read the data.")
      print("\nORIGINAL ERROR MESSAGE:", e)
      exit()

  lr_schedule = lambda epoch: 0.001 if epoch < 75 else 0.0001    # start with lr of 0.001 and then drop to 0.0001 after 75 epochs
  callbacks = [LearningRateScheduler(lr_schedule)]
  if save_model:
      if not os.path.exists(WEIGHTS_DIR): os.mkdir(WEIGHTS_DIR)
      callbacks.append(ModelCheckpoint(filepath=weights_file, monitor='val_loss', save_best_only=True))

  history = model.fit_generator(train_generator, samples_per_epoch / batch_size, nb_epoch, verbose=VERBOSE,
                   callbacks=callbacks, validation_data=val_generator, validation_steps=N_seq_val / batch_size)

  if save_model:
      json_string = model.to_json()
      with open(json_file, "w") as f:
          f.write(json_string)