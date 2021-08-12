+---------------+---------------------+
| STYLE         | BADGE               |
+===============+=====================+
| flat          | |Flat Badge|        |
+---------------+---------------------+


.. |Flat Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=flat


# TEZip
Data data compression tool for time evolutonary data.
## Overview
 Recent advances in Deep Neural Networks (DNNs) have demonstrated a promising potential in predicting the temporal and spatial proximity of time evolutionary data. In this paper, we have developed an effective (de)compression framework called TEZIP that can support dynamic lossy and lossless compression of time evolutionary image frames with high compression ratio and speed. TEZIP first trains a Recurrent Neural Network called PredNet to predict future image frames based on base frames, and then derives the resulting differences between the predicted frames and the actual frames as more compressible delta frames. Next we equip TEZIP with techniques that can exploit spatial locality for the encoding of delta frames and apply lossless compressors on the resulting frames. Furthermore, we introduce window-based prediction algorithms and dynamically pinpoint the trade-off between the window size and the relative errors of predicted frames. Finally, we have conducted an extensive set of tests to evaluate TEZIP. Our experimental results show that, in terms of compression ratio, TEZIP outperforms existing lossless compressors such as x265 by up to 3.2x and lossy compressors such as SZ by up to 3.3x.

# Documents
https://tezip.readthedocs.io/en/latest/

# Publications
* Rupak Roy, Kento Sato, Subhadeep Bhattacharya, Xingang Fang, Yasumasa Joti, Takaki Hatsui, Toshiyuki Hiraki, Jian Guo and Weikuan Yu, “Compression of Time Evolutionary Image Data through Predictive Deep Neural Networks”, In the proceedings of the 21 IEEE/ACM International Symposium on Cluster, Cloud and Internet Computing (CCGrid 2021), May, 2021
* Rupak Roy, Kento Sato, Jian Guo, Jens Domke and Weikuan Yu, “Improving Data Compression with Deep Predictive Neural Network for Time Evolutional Data”, In Proceedings of the International Conference on High Performance Computing, Networking, Storage and Analysis 2019 (SC19), Regular Poster, Denver, USA, Nov, 2019.

