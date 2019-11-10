"""
Plot the proportion of lucid dreams across
all subjects and sessions, at different
DLQ1 cutoffs/criteria.

Also save data and stats dataframes.
"""
from os import path
import pandas as pd

from itertools import combinations
from statsmodels.stats.proportion import proportions_ztest

import matplotlib; matplotlib.use('Qt5Agg') # python3 bug
import matplotlib.pyplot as plt; plt.ion()

import pyplotparams as myplt


resdir = path.expanduser('~/DBp/proj/phenoll/results')
infname = path.join(resdir,'dlq1-frequency.tsv')


########  load and manipulate data  #########

data = pd.read_csv(infname,index_col='subj',sep='\t')

n_reports = data.values.sum() # total number of reports
n_dreams = data.iloc[:,1:].values.sum() # all reports that include dream recall
n_subjs = data.shape[0]

# make a dataframe that has both count and proportion
# for lucidity success based on different criterion.
# note that this is a cumulative sum thing.

# get the cumulative sum of LDs at each cutoff
cumsum_cols = pd.np.roll(data.columns.sort_values(ascending=False),-1).tolist()
cumsum_df = data[cumsum_cols].cumsum(axis=1)

# don't use response of 1 ("Not at all") or "No recall"
# flip it for interpretability
DLQ_COLS = [ f'DLQ1_resp-{i}' for i in range(2,6) ]

index = pd.Index(DLQ_COLS,name='cutoff')
columns = ['dreams_past_cutoff','subjs_past_cutoff']

df = pd.DataFrame(columns=columns,index=index)

df['dreams_past_cutoff'] = cumsum_df[DLQ_COLS].sum(axis=0)
df['subjs_past_cutoff']  = cumsum_df[DLQ_COLS].astype(bool).sum(axis=0)

df['proportion_reports'] = df['dreams_past_cutoff'] / n_reports
df['proportion_dreams'] = df['dreams_past_cutoff'] / n_dreams
df['proportion_subjs'] = df['subjs_past_cutoff'] / n_subjs

for col in df.columns:
    if 'proportion' in col:
        df[col] = df[col].round(2)


#########  stats  #########

n_combos = 3 * len(list(combinations(DLQ_COLS,2)))

dreams_past_cutoff = df['dreams_past_cutoff'].values
n_observations = pd.np.repeat(n_dreams,dreams_past_cutoff.size)

stats_df = pd.DataFrame(index=range(n_combos),
    columns=['evaluation','cutoff_a','cutoff_b','zval','pval'])

i = 0
# compare for all subjs
for cutoffA, cutoffB in combinations(DLQ_COLS,2):
    a = df.loc[cutoffA,'subjs_past_cutoff']
    b = df.loc[cutoffB,'subjs_past_cutoff']
    z, p = proportions_ztest([a,b],[n_subjs,n_subjs])
    stats_df.loc[i,'evaluation'] = 'subjs'
    stats_df.loc[i,['cutoff_a','cutoff_b']] = [cutoffA,cutoffB]
    stats_df.loc[i,['zval','pval']] = [z,p]
    i += 1

# compare for reports and nights
# only thing different here is the n_observations
cond_dict = dict(reports=n_reports,dreams=n_dreams)
for label, n_obs in cond_dict.items():
    for cutoffA, cutoffB in combinations(DLQ_COLS,2):
        a = df.loc[cutoffA,'dreams_past_cutoff']
        b = df.loc[cutoffB,'dreams_past_cutoff']
        z, p = proportions_ztest([a,b],[n_obs,n_obs])
        stats_df.loc[i,'evaluation'] = label
        stats_df.loc[i,['cutoff_a','cutoff_b']] = [cutoffA,cutoffB]
        stats_df.loc[i,['zval','pval']] = [z,p]
        i += 1

# round values while also changing output format to print full values
stats_df['zval'] = stats_df['zval'].map(lambda x: '%.02f' % x)
stats_df['pval'] = stats_df['pval'].map(lambda x: '%.04f' % x)


# export data and results dataframes
df_fname  = path.join(resdir,'induction_success-data.tsv')
stats_fname = path.join(resdir,'induction_success-stats.tsv')
df.to_csv(df_fname,index=True,sep='\t')
stats_df.to_csv(stats_fname,index=False,sep='\t')



#########  draw plot  #########

markers = dict(reports='s',dreams='o',subjs='^')
labels = dict(reports=f'Proportion of all reports ($\mathit{{n}}$={n_reports})',
              dreams=f'Proportion of recalled dreams ($\mathit{{n}}$={n_dreams})',
              subjs=f'Proportion of subjects ($\mathit{{n}}$={n_subjs})')

fig, ax = plt.subplots(figsize=(5,5))

# draw lines and points separately to have diff colored points
for col in df.columns:
    if 'proportion' in col:
        key = col.split('_')[1]
        yvals = df[col].values
        ax.plot(range(2,6),yvals,
            color='k',linestyle='-',linewidth=1,zorder=1)
        ax.scatter(range(2,6),yvals,
            color=[ myplt.dlqcolor(i) for i in range(2,6) ],
            marker=markers[key],edgecolors='w',
            s=150,zorder=2,linewidths=.5)

# handle the xaxis
ax.set_xticks(range(2,6))
xticklabels = [ myplt.DLQ_STRINGS[i] for i in range(2,6) ]
xticklabels = [ x if x == 'Very much' else f'>= {x}'
                for x in xticklabels ]
ax.set_xticklabels(xticklabels,rotation=25)
ax.set_xlabel('Lucid dream criterion')

# handle yaxes
minor_yticks = pd.np.linspace(0,1,21)
major_yticks = pd.np.linspace(0,1,11)
# label yticks with percentages
# major_yticklabels = [ '{:.0f}'.format(x*100) for x in major_yticks ]
ax.set_yticks(minor_yticks,minor=True)
ax.set_xlim(1.5,5.5)
ax.set_ylim(0,1)
ax.set_yticks(major_yticks)
ax.set_ylabel('Lucid dream induction success')
# ax.set_yticklabels(major_yticklabels)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.grid(True,axis='y',which='minor',
        linestyle='--',linewidth=.25,color='k',alpha=1)

# legend for markers
legend_patches = [ matplotlib.lines.Line2D([],[],
                    label=label,marker=markers[key],
                    color='gray',linestyle='none')
                for key, label in labels.items() ]
ax.legend(handles=legend_patches,loc='upper right',
          title='Evaluation',frameon=True,framealpha=1,edgecolor='k')

plt.tight_layout()

for ext in ['png','svg','eps']:
    plot_fname = path.join(resdir,f'induction_success-plot.{ext}')
    plt.savefig(plot_fname)
plt.close()
