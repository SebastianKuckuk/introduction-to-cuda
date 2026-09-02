import shutil
import subprocess
import sys


NSYS_PACKAGE = 'nsight-systems-cli-2026.1.1'

INSTALL_NSYS = f'''
export DEBIAN_FRONTEND=noninteractive

key=/etc/apt/trusted.gpg.d/nvidia-devtools.gpg
list=/etc/apt/sources.list.d/nvidia-devtools.list
repo=https://developer.download.nvidia.com/devtools/repos/ubuntu$(lsb_release -rs | tr -d .)/$(dpkg --print-architecture)/

curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub | gpg --dearmor --yes -o $key
echo "deb [signed-by=$key] $repo /" > $list

# restrict the update to the repository just added - the other sources are up to date already and
# refreshing all of them is slow and prints warnings that have nothing to do with this course
apt-get update -qq -o Dir::Etc::sourcelist=$list -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0
apt-get install -y -qq {NSYS_PACKAGE}
'''


def setup(profiling=False):
    if 'google.colab' not in sys.modules:
        return

    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,compute_cap', '--format=csv,noheader'], capture_output=True, text=True)
    if 0 != gpu.returncode:
        print('No GPU found. Select Runtime > Change runtime type > GPU, then run both setup cells again.')
        return

    if profiling and not shutil.which('nsys'):
        print('Installing Nsight Systems, this takes a moment')

        # -e aborts at the first failing command, pipefail also catches a failing curl in the pipe
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', INSTALL_NSYS], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if 0 != result.returncode:
            print(result.stdout)
            print('Failed to install Nsight Systems, the profiling cells of this notebook will fail.')

    print(f'GPU                {gpu.stdout.strip()}')
    for tool in ['nvcc', 'nsys', 'compute-sanitizer', 'cuda-gdb']:
        print(f'{tool:19}{shutil.which(tool) or "not installed"}')

    if profiling and shutil.which('nsys'):
        version = subprocess.run(['nsys', '--version'], capture_output=True, text=True).stdout.split()[-1]
        print(f'\nOpen the reports generated in this notebook with a local installation of Nsight Systems {version} or newer')
