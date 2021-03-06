"""
Fisher zscore all r values from correlations-zscore.py
and derived pvalues as as the proportion of fisher
zscored R values that are above 0.

Export dataframe holding the final stats
and correlation parameters.

Also save out another resampling file, now with
just an additional column for the fisher zscores.
"""
from os import path
from json import load

import numpy as np
import pandas as pd

from statsmodels.stats.multitest import fdrcorrection


#######  parameter setup  #######

with open('./config.json') as f:
    p = load(f)
    DERIV_DIR = path.expanduser(p['derivatives_directory'])
    FLOAT_FMT = p['float_formatting']
    N_RESAMPLES = p['n_correlation_resamples']

# choose params to make 95% confidence intervals
CI_LO = .025
CI_HI = .975

IMPORT_FNAME = path.join(DERIV_DIR,'correlates.csv')

EXPORT_FNAME_1 = path.join(DERIV_DIR,'correlates-stats.csv')
EXPORT_FNAME_2 = path.join(DERIV_DIR,'correlates_withz.csv')

##################################


#######  load data  #######

res_df = pd.read_csv(IMPORT_FNAME,index_col=['probe','resample'])

###########################


#######  fisher zscore  #######

# fisher zscore all r values
def fisherz(x):
    # arctanh can't handle -1 or 1 so this function accounts for that
    if x in [-1,1]:
        # multiply by x to 
        x -= np.sign(x) * .000001 # picked 6 decimal points bc that's the precision of other values
    return np.arctanh(x)
res_df['fishz'] = res_df['tau'].map(fisherz)

res_df.to_csv(EXPORT_FNAME_2,float_format=FLOAT_FMT,index=True)

################################


#######  run some stats  #######

# initialize stats dataframe with the mean of each metric
stats_df = res_df.groupby('probe').mean()
stats_df.columns = [ f'{c}_mean' for c in stats_df.columns ]
# get confidence intervals for fisherz values
stats_df['fishz_cilo'] = res_df.groupby('probe')['fishz'].quantile(CI_LO)
stats_df['fishz_cihi'] = res_df.groupby('probe')['fishz'].quantile(CI_HI)

# add pvalue based on fisher zscore
def calculate_pvalue(col):
    # p = % of values > or < 0
    # double the smaller p value (bc two-tailed test)
    proportion_above = np.mean( col.values > 0 )
    proportion_below = np.mean( col.values < 0 )
    above_or_below = min([proportion_above,proportion_below])
    pval = 2 * above_or_below
    return pval
stats_df['pval'] = res_df.groupby('probe').agg({'fishz':calculate_pvalue})

# generate a pvalue accounting for multiple comparisons
uncorrected_pvals = stats_df['pval'].values
_, corrp = fdrcorrection(uncorrected_pvals,method='indep',is_sorted=False)
stats_df['pval_corrected'] = corrp

# set it up so everything will be ordered by correlation effect
stats_df.sort_values('pval',ascending=True,inplace=True)

stats_df.to_csv(EXPORT_FNAME_1,float_format=FLOAT_FMT,index=True)

################################
