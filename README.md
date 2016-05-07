# easy_compile #

*easy_compile* is a [Python](https://python.org) script for compiling and running single source C++
programs. It runs on Python from 2.6 to 3.5 and has no external dependencies.

    usage: ec [-h] [-w] [-r] [-f | -C] [-H] [-c | -a | -n] [-v | -q] [-s] [-A PARAMS]
              filename

    Compile & Run a single source file C++ program

    positional arguments:
      filename              file to be compiled

    optional arguments:
      -h, --help            show this help message and exit
      -w, --working         set the working directory to the source file directory
      -r, --release         compile in release mode
      -f, --force           recompile even if up-to-date
      -C, --no-cache        do not use caching at all
      -H, --no-header       do not process headers
      -c, --compile-only    do not run the executable
      -a, --always-report   always print exit code, even if it is zero
      -n, --never-report    never print exit code
      -v, --verbose         produce more output
      -q, --quiet           produce less output
      -s, --stay            wait for any key to be pressed at the end
      -A, --params PARAMS   additional arguments passed to the compiler

    g++ / -std=c++11 -Wall -Wextra -pedantic -Wformat=2 -Wfloat-equal -Wconversion
    -Wcast-qual -Wcast-align -Wuseless-cast -Wlogical-op -Wredundant-decls
    -Wno-shadow -Wno-unused-result -Wno-unused-parameter -Wno-unused-local-typedefs
    -Wno-long-long -DLOCAL_PROJECT / -g -DLOCAL_DEBUG -D_GLIBCXX_DEBUG
    -D_GLIBCXX_DEBUG_PEDANTIC / -O2

### Compiling the script itself ###

If you really need to, you can even compile it with [Cython](http://cython.org): just run
`python waf configure build`. `--check-c-compiler=...` and `--python=...` switches may be used to
specify the exact compiler and interpreter.

Do not expect a huge speed burst however, as the script wasn't specifically optimized for that.
