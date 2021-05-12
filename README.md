# Fourier Transformer and Galerkin Transformer: Attention without softmax
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Pytorch 1.8](https://img.shields.io/badge/pytorch-1.8-blue.svg)](https://pytorch.org/)

This is the repository for paper:


# Requirements
To install requirements:

```setup
pip install -r requirements.txt
```

# Data
The data is courtesy of [Mr. Zongyi Li (Caltech)](https://github.com/zongyi-li): https://github.com/zongyi-li/fourier_neural_operator under the MIT license.

# Examples
All examples are learning PDE-related operators. The setting can be found in [`config.yml`](./config.yml). By default the evaluation is performed on the last 100 samples in the test dataset. All trainers are using the `1cycle` scheduler for 100 epochs.

## Burgers
The baseline benchmark [`ex1_burgers.py`](./ex1_burgers.py): evaluation relative error is about `1e-3` with a simple pointwise forward expansion feature extractor. The input is the initial condition of a viscous Burgers' equation on a discrete grid, the output is an approximation to the solution marched to time $1$. The initial data are generating using a GRF and the data in the validation set are not in the train set.

Default benchmark on a 2048 grid using a Fourier Transformer, with 2 Fourier-type attention layers as encoder and 2 spectral conv layers from [Li et al 2020](https://github.com/zongyi-li/fourier_neural_operator) as decoder:
```bash
python ex1_burgers.py --seed 1127802
```
No subsampling (8192 grid), Galerkin-type attention, adding a diagonal matrix to the Xavier initializations of the `W^Q, W^K, W^V` matrices (about 30% better than those without).
```bash
python ex1_burgers.py --subsample 1\
                      --attn-type 'galerkin'\
                      --xavier-init 0.01 --diag-weight 0.01
```
Use the conventional layer normalization in attention layers:
```python
python ex1_burgers.py --reg-layernorm
```

## Interface Darcy flow
The baseline benchmark [`ex2_darcy.py`](./ex2_darcy.py): evaluation relative error is about `1e-2` with an interpolation-based CNN (CiNN) feature extractor. The coarse grid latent representation is sent to attention layers The operator input is discontinuous coefficient with a random interface sampled at a discrete grid, the output is a finite element approximation to the solution restricted to the sampled grid from a `421x421` grid. The coefficient in the validation set are not in the train set.

Default benchmark on a 141x141 grid using the Galerkin Transformer, 10 Galerkin-type attention layers as encoder and 2 spectral conv layers from [Li et al 2020](https://github.com/zongyi-li/fourier_neural_operator) as decoder. There is a small dropout `5e-2` in the attention layer as well as in the feature extraction layer:
```bash
python ex2_darcy.py
```
For a smaller memory GPU or CPU, please use the 85x85 grid fine, 29x29 coarse grid example:
```bash
python ex2_darcy.py --subsample-attn 15\
                    --subsample-nodes 5\
                    --attn-type 'galerkin'\
                    --xavier-init 0.01 --diag-weight 0.01
```
## Inverse interface coefficient identification for Darcy flow
The baseline benchmark [`ex3_darcy_inv.py`](./ex3_darcy_inv.py): an inverse coefficient identification problem based on the same dataset used in Example 2. However, in this example, the input and the target are reversed, i.e., the target is the interface coefficient with a random geometry, and an optional noise is added to the input. As a limit of the attention operator, the coefficient cannot be resolved at the resolution, the target is of a smaller size than the input.

Default benchmark on a 211x211 fine grid input and a 71x71 coarse grid using the Galerkin Transformer with 6 Galerkin-type attention layers stacked with a simple pointwise feed-forward neural network map the attention output back the desired dimension. There is a small dropout in every key components of the network (`5e-2`). The noise is added to the normalized input, so 0.01 noise means 1%, and 0.1 means 10%.
```bash
python ex3_darcy_inv.py --noise 0.01
```
For a smaller memory GPU, please use the 141x141 grid fine, 36x36 coarse grid, and avoid using the local attention `fourier` or `softmax` in the `--attn-type` switch:
```bash
python ex3_darcy_inv.py --subsample-attn 12\
                        --subsample-nodes 3\
                        --attn-type 'galerkin'\
                        --xavier-init 0.01 --diag-weight 0.01
```

## Memory and speed profiling using `autograd.profiler`
Fourier Transformer features an over 40% reduction in `self_cuda_memory_usage` versus the standard softmax normalized transformers, and Galerkin Transformer doubles the backpropagation speed versus the standard linearized transformers.
```bash
python ex_memory_profile.py --batch-size 4
```

# License
This software is distributed with the MIT license which translates roughly that you can use it however you want and for whatever reason you want. All the
information regarding support, copyright and the license can be found in the [LICENSE](./LICENSE) file.

# Acknowledgement
The hardware to perform this work is provided by Andromeda Saving Fund. This work was supported in part by the National Science Foundation under grants DMS-1913080. We would like to thank [Dr. Long Chen (Univ of California Irvine)](github.com/lyc102) for the inspiration and encouragement on the initial conceiving of this paper, as well as the dedication of [putting nice tutorial on writing beautiful vectorized code](https://github.com/lyc102/ifem). We would like to thank Dr. Ruchi Guo (Univ of California Irvine) and Dr. Yuanzhe Xi (Emory) for feedbacks on the choice of the numerical experiments. We would like to thank the Kaggle community, including but not limited to Jean-François Puget ([Uncle CPMP@Kaggle](https://www.kaggle.com/cpmpml)) and Murakami Akira ([mrkmakr@Kaggle](https://www.kaggle.com/mrkmakr)) for sharing a simple Graph Transformer, daslab@Stanford, OpenVaccine, and Eterna for hosting the COVID-19 mRNA Vaccine competition on Kaggle. We would like to thank [Mr. Zongyi Li (Caltech)](https://github.com/zongyi-li) for sharing some early dev code in the updated PyTorch `torch.fft` interface.  We would like to thank [Joel Schlosser](https://github.com/jbschlosser) to incorporate our change to the PyTorch `transformer` submodule to simplify our testing pipeline.  We would be grateful to the PyTorch community for selflessly code sharing, including Phil Wang([lucidrains@github](https://github.com/lucidrains)) and [Harvard NLP group Klein et al. (2017)](https://nlp.seas.harvard.edu/2018/04/03/attention.html).  Wewould like to thank the chebfun Driscoll et al. (2014) for integrating powerful tools into a simple interface to solve PDEs. We would like to thank [Yannic Kilcher](https://www.youtube.com/c/YannicKilcher/about) and [Hung-yi Lee (National Taiwan University)](https://www.youtube.com/c/HungyiLeeNTU) for frequently covering the newest research on Transformers in video formats.  We would also like to thank the Python community (Van Rossum and Drake (2009); Oliphant (2007))for sharing and developing the tools that enabled this work, including Pytorch Paszke et al.(2017),  NumPy Harris et al. (2020),  SciPy Virtanen et al. (2020),  Plotly Inc. (2015) andMatplotlib Hunter (2007).
