# Regenerate illustrative DSDV/AODV trend charts with numpy and matplotlib.
# Values are model assumptions, not measured network benchmarks.
import numpy as np, matplotlib.pyplot as plt
n=np.array([10,20,30,40,50])
series={'overhead':([18,34,55,78,105],[8,16,28,43,61]),'delay':([24,27,33,41,52],[48,55,63,74,88]),'pdr':([98,97,95,92,89],[96,95,93,90,87])}
for k,(d,a) in series.items():
 x=np.arange(len(n)); w=.36; fig,ax=plt.subplots(); ax.bar(x-w/2,d,w,label='DSDV'); ax.bar(x+w/2,a,w,label='AODV'); ax.set_xticks(x); ax.set_xticklabels(n); ax.set_xlabel('Mobile nodes'); ax.legend(); fig.tight_layout(); fig.savefig('routing_'+k+'.png'); plt.close(fig)
