import matplotlib.pyplot as plt
import numpy as np

from sha_calc import nzs1170p5_spectra
from gmhazard_calc import NZSSoilClass

fig = plt.figure()
ax = fig.gca()
periods = np.exp(np.linspace(np.log(1e-10), np.log(4.5), 1000))
for sc in NZSSoilClass:
    print(sc)

    C, Ch, R, N = nzs1170p5_spectra(periods, 0.3, 20, 1, sc.value)

    ax.plot(periods, Ch)
ax.set_xticks([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5], minor=True)
ax.set_xlim(0, 4.5)
ax.set_ylim(0, 3.5)
ax.set_xlabel('Period, T (s)')
ax.set_ylabel('Spectral shape factor, Ch (T)')
fig.legend(NZSSoilClass)
fig.show()
pass