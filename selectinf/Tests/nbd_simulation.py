from __future__ import print_function

import numpy as np
import pandas as pd
import random
import nose.tools as nt
import collections
collections.Callable = collections.abc.Callable
import sys

from matplotlib import pyplot as plt
import seaborn as sns

from selectinf.nbd_lasso import nbd_lasso
from selectinf.Utils.discrete_family import discrete_family
from selectinf.Tests.instance import GGM_instance

from selectinf.Tests.nbd_naive_and_ds import *

def approx_inference_sim(X, prec, weights_const=1., ridge_const=0., randomizer_scale=1., parallel=False):
    # Precision matrix is in its original order, not scaled by root n
    # X is also in its original order
    n,p = X.shape

    nbd_instance = nbd_lasso.gaussian(X, n_scaled=False, weights_const=weights_const,
                                      ridge_terms=ridge_const, randomizer_scale=randomizer_scale)
    active_signs_random = nbd_instance.fit()
    nonzero = nbd_instance.nonzero

    # Construct intervals
    if nonzero.sum() > 0:
        # Intervals returned is in its original (unscaled) order
        intervals = nbd_instance.inference(parallel=parallel)
        # coverage is upper-triangular
        coverage = get_coverage(nonzero, intervals, prec, n, p, scale=False)
        interval_len = 0
        nonzero_count = 0  # nonzero_count is essentially upper-triangular
        for i in range(p):
            for j in range(i+1,p):
                if nonzero[i,j]:
                    interval = intervals[i,j,:]
                    interval_len = interval_len + (interval[1] - interval[0])
                    nonzero_count = nonzero_count + 1
        avg_len = interval_len / nonzero_count
        cov_rate = coverage.sum() / nonzero_count
        return nonzero, intervals, cov_rate, avg_len
    return None, None, None, None


def nbd_simulations(n=1000, p=30, s=4, proportion=0.5,
                    range=range(0, 100)):
    # Operating characteristics
    oper_char = {}
    oper_char["p"] = []
    oper_char["coverage rate"] = []
    oper_char["avg length"] = []
    oper_char["method"] = []
    oper_char["F1 score"] = []
    oper_char["E size"] = []

    for p in [10, 20, 50]:
        for i in range(range.start, range.stop):
            n_instance = 0
            # print(i)
            # np.random.seed(i)

            while True:  # run until we get some selection
                n_instance = n_instance + 1
                prec,cov,X = GGM_instance(n=200, p=p, max_edges=s)
                n, p = X.shape
                # print((np.abs(prec) > 1e-5))
                noselection = False  # flag for a certain method having an empty selected set

                if not noselection:
                    true_non0 = (prec!=0)
                    for j in range(prec.shape[0]):
                        true_non0[j,j] = False
                    print("Naive")
                    nonzero_n, intervals_n, cov_rate_n, avg_len_n = naive_inference(X, prec,
                                                                                    weights_const=0.5)#, true_nonzero = true_non0)
                    noselection = (nonzero_n is None)
                    # print(nonzero_n)
                    # print(nonzero_n.shape)

                if not noselection:
                    print("DS")
                    nonzero_ds, intervals_ds, cov_rate_ds, avg_len_ds = data_splitting(X, prec, weights_const=0.5,
                                                                                       proportion=proportion)
                    noselection = (nonzero_ds is None)
                    # print(nonzero_ds.shape)
                    if not noselection:
                        print("DS Length:", avg_len_ds)

                if not noselection:
                    print("Approx")
                    nonzero_approx, intervals_approx, cov_rate_approx, avg_len_approx \
                        = approx_inference_sim(X, prec, weights_const=0.5,
                                               ridge_const=1., randomizer_scale=1.,
                                               parallel=False)
                    noselection = (nonzero_approx is None)
                    # print(nonzero_ds.shape)

                if not noselection:
                    # F1 scores
                    # F1_s = calculate_F1_score(beta, selection=nonzero_s)
                    print("symmetric nonzero:", is_sym(nonzero_n))
                    F1_n = calculate_F1_score_graph(prec, selection=nonzero_n)
                    F1_ds = calculate_F1_score_graph(prec, selection=nonzero_ds)
                    F1_approx = calculate_F1_score_graph(prec, selection=nonzero_approx)

                    # Data splitting coverage
                    oper_char["p"].append(p)
                    oper_char["E size"].append(nonzero_ds.sum())
                    oper_char["coverage rate"].append(np.mean(cov_rate_ds))
                    oper_char["avg length"].append(np.mean(avg_len_ds))
                    oper_char["F1 score"].append(F1_ds)
                    oper_char["method"].append('Data Splitting')

                    # Naive coverage
                    oper_char["p"].append(p)
                    oper_char["E size"].append(nonzero_n.sum())
                    oper_char["coverage rate"].append(np.mean(cov_rate_n))
                    oper_char["avg length"].append(np.mean(avg_len_n))
                    oper_char["F1 score"].append(F1_n)
                    oper_char["method"].append('Naive')

                    # Approximate Inference coverage
                    oper_char["p"].append(p)
                    oper_char["E size"].append(nonzero_approx.sum())
                    oper_char["coverage rate"].append(np.mean(cov_rate_approx))
                    oper_char["avg length"].append(np.mean(avg_len_approx))
                    oper_char["F1 score"].append(F1_approx)
                    oper_char["method"].append('Approx')

                    print("# Instances needed for a non-null selection:", n_instance)

                    break  # Go to next iteration if we have some selection

    oper_char_df = pd.DataFrame.from_dict(oper_char)
    oper_char_df.to_csv('GGM_naive_ds_approx' + str(range.start) + '_' + str(range.stop) + '.csv', index=False)

if __name__ == '__main__':
    argv = sys.argv
    start, end = int(argv[1]), int(argv[2])
    # print("start:", start, ", end:", end)
    nbd_simulations(range=range(start, end))