"""
Draw boxplots for each DLQ question.
Across all subjects.

For each DLQ probe, plot a box including
data from all attempts the include recall,
and also a box including only responses
that include non-zero awareness.
"""
from os import path
import pandas as pd

import matplotlib; matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt; plt.ion()

import pyplotparams as myplt


# choose which DLQ probes get plotted
DLQ_COLS = [ f'DLQ:{i}' for i in range(1,20) ]

datadir = path.expanduser('~/IDrive-Sync/proj/phenol/data')
resdir = path.expanduser('~/IDrive-Sync/proj/phenol/results')

infname = path.join(datadir,'data-clean.tsv')
outfname = path.join(resdir,'dlq-boxplots.png')

df = pd.read_csv(infname,sep='\t')

# get rid of dreams without recall
df.dropna(inplace=True)

# extract data for plot, which is just desired DLQ probes
plot_data_all = df[DLQ_COLS].values
plot_data_lim = df.loc[df['DLQ:1']>1,DLQ_COLS].values

# open figure
fig, ax = plt.subplots(figsize=(2*len(DLQ_COLS),6))

# loop over two datasets
for i, data in enumerate([plot_data_all,plot_data_lim]):

    xvals = pd.np.arange(len(DLQ_COLS))
    xvals = xvals-.2 if i==0 else xvals+.2
    facecolor = 'white' if i==0 else 'silver'
    # boxplot
    ax.boxplot(data,widths=.4,positions=xvals,
               patch_artist=True,showbox=True,showfliers=True,
               boxprops={'facecolor':facecolor},
               medianprops={'color':'red'})

# aesthetics
ax.set_xlim(-1,len(DLQ_COLS)+1)
ax.set_xticks(range(len(DLQ_COLS)))
ax.set_xticklabels(DLQ_COLS,rotation=25)
ax.set_xlabel('DLQ probe')
ax.set_ylabel('I was aware that I was dreaming')
ax.set_yticks([1,2,3,4,5])
ax.set_yticklabels(list(myplt.DLQ_STRINGS.values()),rotation=25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True,axis='y',which='major',linestyle='--',
        linewidth=.25,color='k',alpha=1)

plt.tight_layout()

plt.savefig(outfname)
plt.savefig(outfname.replace('png','svg'))
plt.savefig(outfname.replace('png','eps'))
plt.close()
