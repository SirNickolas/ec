cimport cython

cdef inline get_input(cwd, source_name)
cdef inline _init_stdlib()

cdef class Report:
    pass

cdef class Verbosity:
    pass

@cython.locals(wait_for_keystroke=cython.bint)
cdef main()
