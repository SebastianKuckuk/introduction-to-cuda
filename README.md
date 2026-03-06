# Introduction to CUDA C/C++

This repository collects the material for the interactive course *Introduction to CUDA C/C++*.

## Prerequisites

Access to a system with a recent Nvidia GPU, as well as the Nvidia HPC SDK installed.

Profiling data will be obtained on that system.
The generated report files can then be visualized and analyzed locally.
This requires a local installation of Nsight Systems.
It can either be installed [stand-alone](https://developer.nvidia.com/nsight-systems/get-started) (might require a free NVIDIA developer account), or bundled in the [CUDA toolkit](https://developer.nvidia.com/cuda-downloads) or [Nvidia HPC SDK](https://developer.nvidia.com/hpc-sdk-downloads).

A copy of all profiles obtained is also included in this repository.

## Course Content

All course material is collected and available at [https://github.com/SebastianKuckuk/introduction-to-cuda](https://github.com/SebastianKuckuk/introduction-to-cuda) (this repository).

It follows this general agenda:

1. [Introduction](./01-introduction.ipynb)
1. [First GPU Application](./02-first-gpu-application.ipynb)
1. [Porting Applications](./03-porting-applications.ipynb)
1. [GPU Architecture](./04-gpu-architecture.ipynb)
1. [Reductions](./05-reductions.ipynb)
1. [Summary & Outlook](./06-summary-outlook.ipynb)

## Start

To start, clone the repository on your target system (and on your notebook/ workstation to visualize the profiles locally)
```bash
git clone https://github.com/SebastianKuckuk/introduction-to-cuda.git
```

Then head over to the [Introduction](./01-introduction.ipynb) notebook.
