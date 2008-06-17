dnl Process this file with autoconf to produce a configure script.
    stat AC_INIT(sjconf, 1.4.0~dev)

dnl 2.52 is quite realistic
AC_PREREQ(2.52)

AM_INIT_AUTOMAKE([foreign])

sjconflocalstatedir=$localstatedir/lib/sjconf
AC_SUBST([sjconflocalstatedir])

sjconfpluginslocalstatedir=$sjconflocalstatedir/plugins
AC_SUBST([sjconfpluginslocalstatedir])

sjconfconfdir=$sysconfdir/smartjog
AC_SUBST([sjconfconfdir])

sjconfbaseconfdir=$sjconfconfdir/base
AC_SUBST([sjconfbaseconfdir])

sjconfdistribconfdir=$sjconfconfdir/distrib
AC_SUBST([sjconfdistribconfdir])

sjconfcustomconfdir=$sjconfconfdir/custom
AC_SUBST([sjconfcustomconfdir])

sjconftemplatesconfdir=$sjconfconfdir/templates
AC_SUBST([sjconftemplatesconfdir])

AC_CONFIG_FILES([Makefile \
                 doc/Makefile \
                 conf/Makefile \
                 conf/base/Makefile \
                 conf/distrib/Makefile \
                 conf/custom/Makefile \
                 conf/templates/Makefile \
                 setup.py \
                 sjconf \
                 ])

AC_OUTPUT
