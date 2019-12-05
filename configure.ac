dnl Process this file with autoconf to produce a configure script.
AC_PREREQ([2.67])
AC_INIT([sjconf],[1.13.3~dev])

AM_INIT_AUTOMAKE([-Wall 1.11 foreign])

AM_PATH_PYTHON([2.3])
AC_PATH_PROG(TXT2TAGS, txt2tags)

sjconflocalstatedir=$localstatedir/lib/sjconf
AC_SUBST([sjconflocalstatedir])

sjconfpluginslocalstatedir=$sjconflocalstatedir/plugins
AC_SUBST([sjconfpluginslocalstatedir])

sjconfconfdir=$sysconfdir/sjconf
AC_SUBST([sjconfconfdir])

sjconfbaseconfdir=$sjconfconfdir/base
AC_SUBST([sjconfbaseconfdir])

sjconfprofilesconfdir=$sjconfconfdir/profiles
AC_SUBST([sjconfprofilesconfdir])

sjconftemplatesconfdir=$sjconfconfdir/templates
AC_SUBST([sjconftemplatesconfdir])

sjconfpartspythondir=$pythondir/sjconfparts
AC_SUBST([sjconfpartspythondir])

aclocaldir=\$\(datadir\)/aclocal
AC_SUBST([aclocaldir])

autotoolspkgdatadir=\$\(pkgdatadir\)/autotools
AC_SUBST([autotoolspkgdatadir])

AC_CONFIG_FILES([
    Makefile
    doc/Makefile
    conf/Makefile
    conf/base/Makefile
    conf/profiles/Makefile
    conf/templates/Makefile
    conf/bash_completion/Makefile
    sjconfparts/Makefile
    autotools/Makefile
    sjconf
    tests/Makefile
])

AC_OUTPUT
