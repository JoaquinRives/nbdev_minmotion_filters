# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/03_mean_and_spread_filter.ipynb (unless otherwise specified).

__all__ = ['MeanAndSpreadFilter']

# Cell
import numpy as np
import matplotlib.pyplot as plt
from nbdev_minmotion_filters import helpers

# Cell
class MeanAndSpreadFilter:
    """ Applies a moving average filter."""
    def __init__(self, fs = 100., window_length_in_seconds = 1.,no_channels = 1):
        self.N = int(fs * window_length_in_seconds)
        self.window_length_in_seconds = window_length_in_seconds
        self.no_channels = no_channels
        self.circular_buffer = np.zeros((no_channels,self.N))
        self.ind_next = 0 #next available location in the circular buffer
        self.inds_used = 0 #used before the circular buffer has been fully populated
        self.estimated_mean = np.zeros(no_channels)
        self.var_sum = np.zeros(no_channels)
        self.estimated_variance = np.zeros(no_channels)
        self.is_valid_output = False
        self.ready = True

    def reset(self):
        self.ind_next = 0
        self.inds_used = 0
        self.estimated_mean = 0.
        self.var_sum = 0.
        self.estimated_variance = 0.

    def filter_samples(self, s_in, t_in=None):
        res_mean = np.zeros(s_in.shape)
        res_var = np.zeros(s_in.shape)
        if((np.size(s_in) > 0) and self.ready):
            for i in range(s_in.shape[1]):
                x_new = s_in[:,i].copy()
                if(self.inds_used == 0):
                    self.estimated_mean = x_new
                    self.circular_buffer[:,self.ind_next] = x_new
                    self.ind_next += 1
                    self.inds_used += 1
                else:
                    if(self.inds_used < self.N):
                        mean_new = (self.estimated_mean * self.inds_used + x_new) / (self.inds_used + 1.) #Welford's formula
                        self.var_sum += (x_new - self.estimated_mean) * (x_new - mean_new) #
                        self.estimated_mean = mean_new
                        self.estimated_variance = self.var_sum / self.inds_used
                        self.circular_buffer[:,self.ind_next] = x_new
                        self.ind_next += 1
                        self.inds_used += 1
                    else:
                        self.is_valid_output = True
                        self.ind_next = (self.ind_next % self.N)
                        x_old = self.circular_buffer[:,self.ind_next]
                        mean_new = self.estimated_mean + (x_new - x_old) / self.N #Welford's formula
                        self.var_sum += ((x_new - self.estimated_mean) * (x_new - mean_new) - (x_old - self.estimated_mean) * (x_old - mean_new)) #
                        self.estimated_mean = mean_new
                        self.estimated_variance = self.var_sum / self.N
                        self.circular_buffer[:,self.ind_next] = x_new
                        self.ind_next += 1

                res_mean[:,i] = self.estimated_mean.copy()
                res_var[:,i] = self.estimated_variance.copy()

        return res_mean, res_var