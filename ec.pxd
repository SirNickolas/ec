cimport cython

cdef inline get_input(cwd, source_name)

cdef class Report:
    pass

cdef class Verbosity:
    pass

@cython.locals(wait_for_keystroke=cython.bint)
cpdef main()
