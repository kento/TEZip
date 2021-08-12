import hickle as hkl
import numpy as np
import gc
from keras import backend as K
from keras.preprocessing.image import Iterator

# Data generator that creates sequences for input into PredNet.
class SequenceGenerator(Iterator):
    def __init__(self, data_file, source_file, nt,
                 batch_size=8, shuffle=False, seed=None,
                 output_mode='error', sequence_start_mode='all', N_seq=None,
                 data_format=K.image_data_format()):
        self.data_file = data_file
        X = hkl.load(data_file)  # X will be like (n_images, nb_cols, nb_rows, nb_channels)
        self.sources = hkl.load(source_file) # source for each image so when creating sequences can assure that consecutive frames are from same video
        self.nt = nt
        self.batch_size = batch_size
        self.data_format = data_format
        assert sequence_start_mode in {'all', 'unique'}, 'sequence_start_mode must be in {all, unique}'
        self.sequence_start_mode = sequence_start_mode
        assert output_mode in {'error', 'prediction'}, 'output_mode must be in {error, prediction}'
        self.output_mode = output_mode

        if self.data_format == 'channels_first':
            X = np.transpose(X, (0, 3, 1, 2))
        self.im_shape = X[0].shape

        if self.sequence_start_mode == 'all':  # allow for any possible sequence, starting from any frame
            self.possible_starts = np.array([i for i in range(X.shape[0] - self.nt) if self.sources[i] == self.sources[i + self.nt - 1]])
        elif self.sequence_start_mode == 'unique':  #create sequences where each unique frame is in at most one sequence
            curr_location = 0
            possible_starts = []
            while curr_location < X.shape[0] - self.nt + 1:
                if self.sources[curr_location] == self.sources[curr_location + self.nt - 1]:
                    possible_starts.append(curr_location)
                    curr_location += self.nt
                else:
                    curr_location += 1
            self.possible_starts = possible_starts

        if shuffle:
            self.possible_starts = np.random.permutation(self.possible_starts)
        if N_seq is not None and len(self.possible_starts) > N_seq:  # select a subset of sequences if want to
            self.possible_starts = self.possible_starts[:N_seq]
        self.N_sequences = len(self.possible_starts)
        super(SequenceGenerator, self).__init__(len(self.possible_starts), batch_size, shuffle, seed)

    def __getitem__(self, null):
        return self.next()

    def next(self):
        X = hkl.load(self.data_file)
        if self.data_format == 'channels_first':
            X = np.transpose(X, (0, 3, 1, 2))
        
        with self.lock:
            current_index = (self.batch_index * self.batch_size) % self.n
            index_array, current_batch_size = next(self.index_generator), self.batch_size
        batch_x = np.zeros((current_batch_size, self.nt) + self.im_shape, np.float32)
        for i, idx in enumerate(index_array):
            idx = self.possible_starts[idx]
            batch_x[i] = self.preprocess(X[idx:idx+self.nt])
        if self.output_mode == 'error':  # model outputs errors, so y should be zeros
            batch_y = np.zeros(current_batch_size, np.float32)
        elif self.output_mode == 'prediction':  # output actual pixels
            batch_y = batch_x

        del X
        gc.collect()
        
        return batch_x, batch_y

    def preprocess(self, X):
        return X.astype(np.float32) / 255


def data_padding(X_test):
    
    image_pick = X_test[0, 0]
    height = image_pick.shape[0]
    width = image_pick.shape[1]

    desired_im_sz = padding_shape(height, width)


    X = np.zeros((X_test.shape[0], X_test.shape[1], desired_im_sz[0], desired_im_sz[1], X_test.shape[4]))

    for i in range(X_test.shape[0]):
        for j in range(X_test.shape[1]):
            X[i, j, :X_test.shape[2], :X_test.shape[3]] = X_test[i, j]

    return X


def padding_shape(height, width):
    padding_height = padding_size(height)
    padding_width = padding_size(width)
    padding_shape_result = (padding_height, padding_width)

    return padding_shape_result


def padding_size(num):
    if num % 8 == 0:
        return num
    padding_num = int(num / 8)
    return (padding_num + 1) * 8