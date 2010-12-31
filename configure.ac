dnl Process this file with autoconf to produce a configure script.
AC_INIT(sjconf, 1.10.0)

dnl 2.52 is quite realistic
AC_PREREQ(2.52)

AM_INIT_AUTOMAKE([foreign])

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

AC_CONFIG_FILES([Makefile \
                 doc/Makefile \
                 conf/Makefile \
                 conf/base/Makefile \
                 conf/profiles/Makefile \
                 conf/templates/Makefile \
                 sjconfparts/Makefile \
                 autotools/Makefile \
                 sjconf \
                 ])

AC_OUTPUT
