=======
 SJConf
=======

SJConf is a configuration editing tool written in Python.

SJConf handles global and server specific configuration, deployment
and service restart.

SJConf in itself does not have any knowledge of configuration files
and their settings, everything is done through the use of plugins.


License
=======

SJConf is released under the `GNU LGPL 2.1 <http://www.gnu.org/licenses/lgpl-2.1.html>`_.


Build and installation
=======================

Bootstrapping
-------------

SJConf uses the autotools for its build system.

If you checked out code from the git repository, you will need
autoconf and automake to generate the configure script and Makefiles.

To generate them, simply run::

    $ autoreconf -fvi

Building
--------

SJConf builds like your typical autotools-based project::

    $ ./configure && make && make install


Development
===========

We use `semantic versioning <http://semver.org/>`_ for
versioning. When working on a development release, we append ``~dev``
to the current version to distinguish released versions from
development ones. This has the advantage of working well with Debian's
version scheme, where ``~`` is considered smaller than everything (so
version 1.10.0 is more up to date than 1.10.0~dev).


Authors
=======

SJConf was started at SmartJog by Philippe Bridant. Most of the code
was heavily redesigned by Jean-Philippe Garcia Ballester in 2008 to
give it its current API / class hierarchy. Various employees and
interns from SmartJog fixed bugs and added features since then.

* Alexandre Bossard
* Alexandre Bique
* Benoit Mauduit
* Clément Gauthey
* Gilles Dartiguelongue
* Grégory Charbonneau
* Jean-Baptiste Denis
* Jean-Philippe Garcia Ballester
* Mathieu Dupuy
* Matthieu Bouron
* Nicolas Noirbent
* Philippe Bridant
* Rémi Cardona
* Thomas Sanchez
* Nicolas Delvaux <nicolas.delvaux@cji.paris>
