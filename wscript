APPNAME = "ec"
VERSION = "1.1"


def options(opt):
    opt.load("compiler_c")
    opt.load("python")
    opt.load("cython")


def configure(cnf):
    cnf.load("compiler_c")
    cnf.load("python")
    cnf.load("cython")
    cnf.check_python_headers()

    cnf.env.CYTHONFLAGS = ["--embed", "--annotate", "--fast-fail"]
    cnf.env.CFLAGS      = ["-O3"]
    cnf.env.LINKFLAGS   = ["-s"]


def build(bld):
    bld(
        rule="${CYTHON} ${CYTHONFLAGS} -o ${TGT} ${SRC}",
        source="src/ec.py",
        target="ec.c",
    )

    bld.program(
        features="pyembed",
        source="ec.c",
        target=APPNAME,
    )


def dist(dst):
    patterns = [".git"]
    warned = False
    with open(".gitignore") as f:
        for line in f:
            line = line.strip()
            if line:
                if line.startswith('/'):
                    patterns.append(line[1:])
                elif not line.startswith('!'):
                    patterns.append("**/" + line)
                elif not warned:
                    from waflib import Logs
                    Logs.warn(".gitignore is most likely to be processed incorrectly")
                    warned = True

    dst.excl = patterns
