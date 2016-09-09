#!/usr/bin/env python

from __future__ import print_function

import argparse
import itertools
import os
import re
import shlex
import subprocess
import sys
import tempfile


COMPILER = R"g++"

COMMON_OPTIONS = r"""
    -Wall -Wextra -pedantic -Wformat=2 -Wfloat-equal -Wlogical-op -Wredundant-decls
    -Wconversion -Wcast-qual -Wcast-align -Wuseless-cast
    -Wno-shadow -Wno-unused-result -Wno-unused-parameter -Wno-unused-local-typedefs -Wno-long-long
    -DLOCAL_PROJECT
"""

# COMPILER = R"clang++"

# COMMON_OPTIONS = r"""
#     -Weverything
#     -Wno-c++98-compat-pedantic
#     -Wno-missing-variable-declarations
#     -Wno-missing-prototypes
#     -Wno-padded
#     -Wno-global-constructors
#     -Wno-exit-time-destructors
#     -Wno-old-style-cast
#     -Wno-sign-conversion
#     -Wno-shadow
#     -Wno-gnu-statement-expression
#     -Wno-gnu-label-as-value
#     -Wno-dollar-in-identifier-extension
#     -Wno-long-long
#     -Wno-switch-enum
#     -Wno-format-nonliteral
#     -Wno-format-security
#     -Wno-unused-parameter
#     -Wno-unused-result
#     -Wno-unused-macros
#     -Wno-unused-local-typedefs
#     -DLOCAL_PROJECT
# """

DEBUG_OPTIONS   = "-g -DLOCAL_DEBUG -D_GLIBCXX_DEBUG -D_GLIBCXX_DEBUG_PEDANTIC"
RELEASE_OPTIONS = "-O2"

CACHE = os.path.join(tempfile.gettempdir(), ".ec")

FALLBACK_EXTENSIONS = (".cpp", ".cxx", ".cc", ".c")

SUMMARY = " / ".join((COMPILER, COMMON_OPTIONS, DEBUG_OPTIONS, RELEASE_OPTIONS))


def get_input(cwd, source_name):
    # return os.path.join(cwd, "input.txt")
    return os.path.join(cwd, os.path.splitext(source_name)[0] + ".in")


HEADER_TEMPLATE = "#include <%s>//\n" # Must not contain regex characters with special meaning.

STDLIB = {
    "algorithm": """
        all_of any_of none_of for_each find find_if find_if_not find_end find_first_of adjacent_find
        count count_if mismatch equal is_permutation search search_n copy copy_n copy_if
        copy_backward move move_backward swap swap_ranges iter_swap transform replace replace_if
        replace_copy replace_copy_if fill fill_n generate generate_n remove remove_if remove_copy
        remove_copy_if unique unique_copy reverse reverse_copy rotate rotate_copy random_shuffle
        shuffle is_partitioned partition stable_partition partition_copy partition_point sort
        stable_sort partial_sort partial_sort_copy is_sorted is_sorted_until nth_element lower_bound
        upper_bound equal_range binary_search merge inplace_merge includes set_union
        set_intersection set_difference set_symmetric_difference push_heap pop_heap make_heap
        sort_heap is_heap is_heap_until min max minmax min_element max_element minmax_element
        lexicographical_compare next_permutation prev_permutation
    """,
    "array": "array",
    "bitset": "bitset",
    "cassert": "assert",
    "cctype": """
        isalnum isalpha isblank iscntrl isdigit isgraph islower isprint ispunct isspace isupper
        isxdigit tolower toupper
    """,
    "cfloat": """
        FLT_RADIX FLT_MANT_DIG DBL_MANT_DIG LDBL_MANT_DIG FLT_DIG DBL_DIG LDBL_DIG FLT_MIN_EXP
        DBL_MIN_EXP LDBL_MIN_EXP FLT_MAX_EXP DBL_MAX_EXP LDBL_MAX_EXP FLT_MAX DBL_MAX LDBL_MAX
        FLT_EPSILON DBL_EPSILON LDBL_EPSILON FLT_MIN DBL_MIN LDBL_MIN FLT_ROUNDS FLT_EVAL_METHOD
        DECIMAL_DIG
    """,
    "climits": """
        CHAR_BIT SCHAR_MIN SCHAR_MAX UCHAR_MAX CHAR_MIN CHAR_MAX MB_LEN_MAX SHRT_MIN SHRT_MAX
        USHRT_MAX INT_MIN INT_MAX UINT_MAX LONG_MIN LONG_MAX ULONG_MAX LLONG_MIN LLONG_MAX
        ULLONG_MAX
    """,
    "cmath": """
        cos sin tan acos asin atan atan2 cosh sinh tanh acosh asinh atanh exp frexp ldexp log log10
        modf exp2 expm1 ilogb log1p log2 logb scalbn scalbln pow sqrt cbrt hypot erf erfc tgamma
        lgamma ceil floor fmod trunc round lround llround rint lrint llrint nearbyint remainder
        remquo copysign nan nextafter nexttoward fdim fmax fmin fabs fma fpclassify isfinite isinf
        isnan isnormal signbit isgreater isgreaterequal isless islessequal islessgreater isunordered
        math_errhandling INFINITY NAN HUGE_VAL HUGE_VALF HUGE_VALL MATH_ERRNO MATH_ERREXCEPT
        FP_FAST_FMA FP_FAST_FMAF FP_FAST_FMAL FP_INFINITE FP_NAN FP_NORMAL FP_SUBNORMAL FP_ZERO
        FP_ILOGB0 FP_ILOGBNAN double_t float_t
    """,
    "complex": "complex",
    "csetjmp": "longjmp setjmp jmp_buf",
    "cstdio": """
        rename tmpfile tmpnam fclose fflush fopen freopen setbuf setvbuf fprintf fscanf printf scanf
        sprintf sscanf vfprintf vprintf vsprintf fgetc fgets fputc fputs getc getchar gets putc
        putchar puts ungetc fread fwrite fgetpos fseek fsetpos ftell rewind clearerr feof ferror
        perror BUFSIZ EOF FILENAME_MAX FOPEN_MAX L_tmpnam TMP_MAX _IOFBF _IOLBF _IONBF SEEK_CUR
        SEEK_END SEEK_SET FILE fpos_t
    """,
    "cstdlib": """
        atof atoi atol atoll strtod strtof strtol strtold strtoll strtoul strtoull rand srand calloc
        free malloc realloc abort atexit exit getenv system bsearch qsort abs div labs ldiv llabs
        lldiv mblen mbtowc wctomb mbstowcs wcstombs EXIT_FAILURE EXIT_SUCCESS MB_CUR_MAX NULL
        RAND_MAX div_t ldiv_t lldiv_t size_t
    """,
    "cstring": """
        memcpy memmove strcpy strncpy strcat strncat memcmp strcmp strcoll strncmp strxfrm memchr
        strchr strcspn strpbrk strrchr strspn strstr strtok memset strerror strlen
    """,
    "ctime": """
        clock difftime mktime time asctime ctime gmtime localtime strftime CLOCKS_PER_SEC clock_t
        time_t tm
    """,
    "deque": "deque",
    "exception": """
        exception bad_exception nested_exception exception_ptr terminate_handler unexpected_handler
        terminate get_terminate set_terminate unexpected get_unexpected set_unexpected
        uncaught_exception current_exception rethrow_exception make_exception_ptr throw_with_nested
        rethrow_if_nested
    """,
    "forward_list": "forward_list",
    "fstream": "ifstream ofstream fstream filebuf",
    "functional": """
        unary_function binary_function plus minus multiplies divides modulus negate equal_to
        not_equal_to greater less greater_equal less_equal logical_and logical_or logical_not not1
        not2 bind1st bind2nd ptr_fun mem_fun mem_fun_ref unary_negate binary_negate binder1st
        binder2nd pointer_to_unary_function pointer_to_binary_function mem_fun_t mem_fun1_t
        const_mem_fun_t const_mem_fun1_t mem_fun_ref_t mem_fun1_ref_t const_mem_fun_ref_t
        const_mem_fun1_ref_t bind cref mem_fn ref function reference_wrapper bit_and bit_or bit_xor
        bad_function_call hash is_bind_expression is_placeholder placeholders
    """,
    "initializer_list": "initializer_list",
    "iomanip": """
        setiosflags resetiosflags setbase setfill setprecision setw get_money put_money get_time
        put_time
    """,
    "iostream": "ios_base ios istream ostream iostream streambuf cin cout cerr clog",
    "iterator": """
        advance distance back_inserter front_inserter inserter iterator iterator_traits
        reverse_iterator back_insert_iterator front_insert_iterator insert_iterator istream_iterator
        ostream_iterator istreambuf_iterator ostreambuf_iterator input_iterator_tag
        output_iterator_tag forward_iterator_tag bidirectional_iterator_tag
        random_access_iterator_tag
    """,
    "limits": "numeric_limits float_round_style float_denorm_style",
    "list": "list",
    "map": "map multimap",
    "memory": """
        allocator allocator_arg allocator_arg_t allocator_traits auto_ptr auto_ptr_ref shared_ptr
        weak_ptr unique_ptr default_delete make_shared allocate_shared static_pointer_cast
        dynamic_pointer_cast const_pointer_cast get_deleter owner_less enable_shared_from_this
        raw_storage_iterator get_temporary_buffer return_temporary_buffer uninitialized_copy
        uninitialized_copy_n uninitialized_fill uninitialized_fill_n pointer_traits pointer_safety
        declare_reachable undeclare_reachable declare_no_pointers undeclare_no_pointers
        get_pointer_safety align addressof
    """,
    "numeric": "accumulate adjacent_difference inner_product partial_sum iota",
    "queue": "queue priority_queue",
    "set": "set multiset",
    "sstream": "istringstream ostringstream stringstream stringbuf",
    "stack": "stack",
    "stdexcept": """
        logic_error domain_error invalid_argument length_error out_of_range runtime_error
        range_error overflow_error underflow_error
    """,
    "string": """
        basic_string char_traits string u16string u32string wstring stoi stol stoul stoll stoull
        stof stod stold to_string to_wstring
    """,
    "tuple": "tuple tuple_size tuple_element make_tuple forward_as_tuple tuple_cat",
    "typeinfo": "type_info bad_cast bad_typeid",
    "unordered_map": "unordered_map unordered_multimap",
    "unordered_set": "unordered_set unordered_multiset",
    "utility": """
        make_pair forward move_if_noexcept declval pair piecewise_construct_t piecewise_construct
        rel_ops
    """,
    "valarray": "valarray slice gslice slice_array gslice_array mask_array indirect_array",
    "vector": "vector",
}

# TODO: Add caching.
SYMBOL_MAPPING = { }

def _init_stdlib():
    ls = [ ]
    m = SYMBOL_MAPPING
    for header, symbols in STDLIB.items():
        symbols = symbols.split()
        ls += symbols
        for sym in symbols:
            m[sym] = header

    return re.compile(r"^%s|\b(?:%s)\b" % (HEADER_TEMPLATE % r"(.*)", '|'.join(ls)), re.M)

RX = _init_stdlib()


class Report:
    never  = 1
    normal = 2
    always = 3


class Verbosity:
    quiet   = 1
    normal  = 2
    verbose = 3


try:
    ProcessLookupError
except NameError:
    class ProcessLookupError(OSError):
        pass


def main():
    wait_for_keystroke = False
    try:
        parser = argparse.ArgumentParser(epilog=SUMMARY, description="""
            Compile & Run a single source file C++ program
        """)
        parser.add_argument("-w", "--working", action="store_true", help="""
            set the working directory to the source file directory
        """)
        parser.add_argument("-r", "--release", action="store_true", help="""
            compile in release mode
        """)
        parser.add_argument("-3", "--cpp03",
            action="store_const", dest="std", const="c++03", help="""
            follow the C++03 language standard (default is C++11)
        """)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-f", "--force", action="store_true", help="""
            recompile even if up-to-date
        """)
        group.add_argument("-C", "--no-cache", action="store_true", help="""
            do not use caching at all
        """)
        parser.add_argument("-H", "--no-header", action="store_true", help="""
            do not process headers
        """)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-c", "--compile-only", action="store_true", help="""
            do not run the executable
        """)
        group.add_argument("-a", "--always-report",
            action="store_const", dest="report", const=Report.always, help="""
            always print exit code, even if it is zero
        """)
        group.add_argument("-n", "--never-report",
            action="store_const", dest="report", const=Report.never, help="""
            never print exit code
        """)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose",
            action="store_const", dest="verbosity", const=Verbosity.verbose, help="""
            produce more output
        """)
        group.add_argument("-q", "--quiet",
            action="store_const", dest="verbosity", const=Verbosity.quiet, help="""
            produce less output
        """)
        parser.add_argument("-s", "--stay", action="store_true", help="""
            wait for any key to be pressed at the end
        """)
        parser.add_argument("filename", help="""
            file to be compiled
        """)
        parser.add_argument("-A", "--params", action="append", default=[ ], help="""
            additional arguments passed to the compiler
        """)

        parser.set_defaults(std="c++11", report=Report.normal, verbosity=Verbosity.normal)

        if len(sys.argv) <= 1:
            parser.print_help()
            return

        args = parser.parse_args()

        src = args.filename
        base, ext = os.path.splitext(src)
        found = False
        if not ext:
            for fallback in FALLBACK_EXTENSIONS:
                f = base + fallback
                if os.path.isfile(f):
                    src = f
                    found = True
                    break

        if not found and not os.path.isfile(src):
            print("No such file: %r" % src, file=sys.stderr)
            wait_for_keystroke = args.stay
            sys.exit(1)

        src = os.path.realpath(src)

        if args.working:
            os.chdir(os.path.dirname(src))

        cache = None if args.no_cache else CACHE
        verbosity = args.verbosity

        binary_suffix = ".exe" if sys.platform.startswith("win") else ""
        binary = os.path.splitext(os.path.basename(src))[0] + binary_suffix
        compilation_needed = True

        if cache:
            import hashlib

            hasher = hashlib.sha512()
            hashing_needed = True

        if not args.no_header:
            with open(src) as f:
                contents = f.read()

            headers = set()
            existing_headers = set()
            prev_pos = 0
            modified = [ ]
            at_the_top = False
            sym_mapping = SYMBOL_MAPPING
            for m in RX.finditer(contents):
                h = sym_mapping.get(m.group())
                if h is not None:
                    headers.add(h)
                else:
                    existing_headers.add(m.group(1))
                    if m.start() == 0:
                        at_the_top = True
                    if prev_pos != m.start():
                        modified.append(contents[prev_pos:m.start()])
                    prev_pos = m.end()

            if prev_pos != 0 and headers != existing_headers:
                if verbosity >= Verbosity.verbose:
                    print("Rewriting...")
                    sys.stdout.flush()

                modified.append(contents[prev_pos:])
                with open(src, "w") as f:
                    if not at_the_top:
                        f.write(modified[0])
                    template = HEADER_TEMPLATE
                    for h in sorted(headers):
                        f.write(template % h)
                    for chunk in itertools.islice(modified, not at_the_top, None):
                        f.write(chunk)

        if cache:
            import shutil

            drive, path = os.path.splitdrive(src)
            cache_base = os.path.join(cache, drive[:-1], path[1:])
            cached_binary = cache_base + (".release" if args.release else ".debug")
            cached_digest = cached_binary + ".src"

            if hashing_needed:
                with open(src, "rb") as f:
                    while True:
                        b = f.read(4096)
                        if not b:
                            break
                        hasher.update(b)

            new_digest = hasher.digest()

            if not args.force and os.path.isfile(cached_digest) and os.path.isfile(cached_binary):
                with open(cached_digest, "rb") as f:
                    if f.read(len(new_digest)) == new_digest:
                        compilation_needed = False

        if compilation_needed:
            if verbosity >= Verbosity.normal:
                print("Compiling...")
                sys.stdout.flush()

            params = [COMPILER]
            params += shlex.split(COMMON_OPTIONS, comments=True)
            params += shlex.split(RELEASE_OPTIONS if args.release else DEBUG_OPTIONS, comments=True)
            params += ["-std=%s" % args.std, "-o", binary, os.path.relpath(src)]
            for user_defined in args.params:
                params += shlex.split(user_defined, comments=True)

            if verbosity >= Verbosity.verbose:
                print(params)
                sys.stdout.flush()

            try:
                ret = subprocess.call(params)
            except ProcessLookupError:
                raise
            except OSError:
                try:
                    subprocess.check_call([COMPILER, "--version"])
                except OSError:
                    print("Cannot run a compiler: %r" % params, file=sys.stderr)
                    wait_for_keystroke = args.stay
                    sys.exit(1)
                else:
                    raise ProcessLookupError

            wait_for_keystroke = args.stay
            if ret != 0:
                sys.exit(ret)

            if cache:
                try:
                    os.makedirs(os.path.dirname(cache_base))
                except OSError:
                    pass

                shutil.copy2(binary, cached_binary)
                with open(cached_digest, "wb") as f:
                    f.write(new_digest)

            if verbosity >= Verbosity.normal:
                print("Done.")
                sys.stdout.flush()
        else:
            assert cache
            shutil.copy2(cached_binary, binary)
            wait_for_keystroke = args.stay

        if not args.compile_only:
            input_file = get_input(os.path.curdir, os.path.basename(src))
            try:
                with open(input_file, "rb") as f:
                    ret = subprocess.call(os.path.join(os.path.curdir, binary), stdin=f)
            except IOError:
                print("Input file is not found: %r" % input_file, file=sys.stderr)
                sys.exit(1)

            if (ret != 0 and args.report != Report.never) or args.report == Report.always:
                print()
                print("Process terminated with code", ret)

            sys.exit(ret)

    except (KeyboardInterrupt, ProcessLookupError):
        if verbosity >= Verbosity.normal:
            print("^C" if sys.platform.startswith("win") else "")
        sys.exit(1)

    finally:
        if wait_for_keystroke:
            try:
                import termios, tty
            except ImportError:
                import msvcrt
                msvcrt.getch()
            else:
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()
