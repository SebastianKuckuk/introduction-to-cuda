import argparse
import os
import pathlib
import subprocess

from IPython import get_ipython
import IPython.core.magic as magic


@magic.magics_class
class ICEMagic(magic.Magics):
    @staticmethod
    def indent_lines(to_indent, indent=4*' ', indent_pragma=True):
        return '\n'.join(l if (not indent_pragma and l.startswith('#')) or not l else indent + l for l in to_indent.split('\n'))        

    
    @staticmethod
    def create_path_for_file(file):
        pathlib.Path(file[:file.rindex(os.path.sep)]).mkdir(parents=True, exist_ok=True)


    def __init__(self, shell):
        super(ICEMagic, self).__init__(shell)
        self.argparsers = {
            'base'       : argparse.ArgumentParser(description='ICE magic for serial C++ code'),
            'cuda'       : argparse.ArgumentParser(description='ICE magic for CUDA C++ code'),
            'omp'        : argparse.ArgumentParser(description='ICE magic for OpenMP parallel C++ code'),
            'omp-target' : argparse.ArgumentParser(description='ICE magic for C++ code with OpenMP target offloading'),
        }

        # query TMPDIR
        env = os.environ
        tmpdir = env['HOME']
        if 'TMPDIR' in env:
            tmpdir = env['TMPDIR']
        print(f'Using temporary directory {tmpdir}')

        # set magic arguments with common default values
        for p in self.argparsers.values():
            p.add_argument('-v', '--verbose', help='prints each command executed', action='store_true', default=False)
            p.add_argument('-d', '--display', help='displays the generated application code', action='store_true', default=False)
            p.add_argument('-c', '--code-file', help='specifies the output source code file', default=tmpdir+'/code.cpp')
            p.add_argument('-b', '--binary', help='specifies the compiled binary file', default=tmpdir+'/app')
            p.add_argument('-e', '--env', help='sets environment variables for execution', nargs='+', default={})
            p.add_argument('-t', '--time', help='generates additional timing code', action='store_true', default=False)
            p.add_argument('-f', '--flags', help='sets additional compiler flags to be used', nargs='+', default=[])
            p.add_argument('-i', '--include', help='specifies additional includes to be added', nargs='+', default=[])
            p.add_argument('-p', '--profile', help='profiles the application with Nsight Systems', action='store_true', default=False)
            p.add_argument('-o', '--profile-file', help='specifies the profile output file', default='')

        # set magic arguments with specialized default values
        for case, compiler in { 'base' : 'g++', 'cuda' : 'nvcc', 'omp' : 'g++', 'omp-target' : 'nvc++' }.items():
            self.argparsers[case].add_argument('--compiler', help='specifies the compiler to be used', default=compiler)

        # get compute capability for cuda case
        cc_text = subprocess.run(['nvidia-smi', '--query-gpu=compute_cap', '--format=csv,noheader'], capture_output=True)
        compute_capability = cc_text.stdout.decode('utf-8').strip().replace('.', '')

        for case, flags in { 'base' : ['O3', 'march=native', 'std=c++17', 'Wall'],
                                'cuda' : ['O3', f'arch=sm_{compute_capability}'],
                                'omp' : ['O3', 'march=native', 'std=c++17', 'Wall', 'fopenmp'],
                                'omp-target' : ['O3', 'std=c++17', 'mp=gpu'] }.items():
            self.argparsers[case].add_argument('-F', '--def-flags', help='overwrites default compiler flags to be used', nargs='+', default=flags)

        # iostream is required for printing
        # chrono and thread are required for sleeping
        # omp.h is required for OpenMP API functions
        for case, includes in { 'base' : ['iostream', 'iomanip', 'chrono', 'thread'],
                                'cuda' : ['iostream', 'iomanip', 'chrono', 'thread', 'cuda/cmath', 'code/util.h'],
                                'omp' : ['iostream', 'iomanip', 'chrono', 'thread', 'omp.h'],
                                'omp-target' : ['iostream', 'iomanip', 'chrono', 'thread', 'omp.h'] }.items():
            self.argparsers[case].add_argument('-I', '--def-include', help='overwrites default includes to be added', nargs='+', default=includes)

        # store current (last) argument configuration, init with default values
        self.args = self.argparsers['base'].parse_args([])
        # store current (last) code snippet passed, init with empty values
        self.code = ''


    def generate_application(self):
        cleaned = self.code
        cleaned = '\n'.join(l.replace('👆', '').rstrip() for l in cleaned.split('\n') if '👆' not in l or l.replace('👆', '').strip())
        cleaned = cleaned.strip()
        
        if not self.args.time:
            wrapped = cleaned
        else:
            wrapped = \
'''auto start = omp_get_wtime();

''' + cleaned + '''

auto end = omp_get_wtime();
std::cout << "Total time: " << 1e3 * (end - start) << " ms" << std::endl;'''

        return '\n'.join(f'#include <{i}>' for i in self.args.def_include + self.args.include) + '''

''' + wrapped


    def generate_markdown(self):
        return f'''```c++
{self.generate_application()}
```'''


    def wrap_compile_exec(self):
        app_code = self.generate_application()

        # write code to file
        if self.args.verbose:
            print(f'Writing to       {self.args.code_file}')

        __class__.create_path_for_file(self.args.code_file)

        with open(self.args.code_file, 'w+') as f:
            print(app_code, file=f)

        # compile code
        __class__.create_path_for_file(self.args.binary)

        cmdline = [self.args.compiler] + [f'-{f}' for f in self.args.def_flags + self.args.flags] + ['-o', self.args.binary, self.args.code_file]
        if self.args.verbose:
            print(f'Compiling with   {" ".join(cmdline)}')

        subprocess.check_call(cmdline)

        # prefix binary with nsys if required
        bin_call = [self.args.binary]
        if self.args.profile:
            add_args = []
            if self.args.profile_file:
                add_args = ['-o', self.args.profile_file, '--force-overwrite=true']
            bin_call = ['nsys', 'profile', '--stats=true'] + add_args + bin_call

        # execute binary
        if 0 == len(self.args.env):
            if self.args.verbose:
                print(f'Executing        {" ".join(bin_call)}')
                print()

            subprocess.check_call(bin_call)
        else:
            env = os.environ.copy()
            for e in self.args.env:
                var, val = e.split('=')
                env[var] = val

            if self.args.verbose:
                print(f'Executing        {" ".join(self.args.env)} {" ".join(bin_call)}')
                print()

            subprocess.check_call(bin_call, env=env)


    def ice(self, line, cell, parser_case):
        # wrap in try ... except to catch sys exit raised when -h or --help is used
        try:
            self.args = self.argparsers[parser_case].parse_args(line.split())
        except SystemExit:
            return

        self.code = cell

        if self.args.display:
            self.display_cpp(line)

        self.wrap_compile_exec()


    @magic.cell_magic
    def cpp(self, line, cell):
        self.ice(line, cell, 'base')


    @magic.cell_magic
    def cuda(self, line, cell):
        self.ice(line, cell, 'cuda')


    @magic.cell_magic
    def cpp_omp(self, line, cell):
        self.ice(line, cell, 'omp')

 
    @magic.cell_magic
    def cpp_omp_target(self, line, cell):
        self.ice(line, cell, 'omp-target')

    
    @magic.line_magic
    def display_cpp(self, line):
        get_ipython().run_cell_magic('markdown', '', self.generate_markdown())


# register magic with a running IPython
def load_ipython_extension(ipython):
    """
    can be loaded via `%load_ext path.ice.magic` or be configured to be autoloaded by IPython at startup time
    """

    # IPython will call the default constructor on it - no need to instantiate
    ipython.register_magics(ICEMagic)
