from conans import ConanFile, tools
from conans.errors import ConanException
from conans.util.files import load
from conans.client.file_copier import FileCopier
import os
import re

class GearmanConan(ConanFile):
    name = "Gearman"
    version = "1.1.15"
    license = "BSD"
    url = "https://github.com/kmaragon/conan-gearman"
    description = "libgearman package for Conan"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            "shared": [True, False],
            "server": [True, False]
        }

    requires = "Boost/1.60.0@lasote@stable","libevent/2.0.22@theirix/stable"
    default_options = "shared=False","server=False"
    generators = "gcc"
    libcxx = "stdc++"

    def configure(self):
        self.options["Boost"].shared = True
        self.options["Boost"].header_only = False

    def source(self):
        tools.download("https://github.com/gearman/gearmand/releases/download/%(1)s/gearmand-%(1)s.tar.gz" % {'1': self.version},
                    "gearman.tar.gz")

        tools.unzip("gearman.tar.gz")
        os.unlink("gearman.tar.gz")

    def build(self):
        # extract the boost lib dir
        boost_libdir=""
        finished_package = os.getcwd() + "/pkg"

        flags = load("conanbuildinfo.gcc").split()
        for fl in flags:
            if fl[0:2] == '-L' and re.match('.*[^A-Za-z0-9_\\-]Boost[^A-Za-z0-9_\\-]', fl):
                boost_libdir = fl[2:]

        make_options = os.getenv("MAKEOPTS") or ""
        if not re.match("/[^A-z-a-z_-]-j", make_options):
            cpucount = tools.cpu_count()
            make_options += " -j %s" % (cpucount * 2)

        shared_flags = '--enable-static --disable-shared' if not self.options.shared else '--disable-static'
        cflags = "-I%s/../include" % boost_libdir
        os.environ["CFLAGS"] = cflags
        os.environ["CXXFLAGS"] = cflags
        os.environ["LDFLAGS"] = "-L%s" % boost_libdir

        if self.options.server:
            os.environ["LDFLAGS"] += " -Wl,-E"

        if not self.options.shared:
            os.environ["LIBS"] = "-l%s" % self.libcxx

        self.run("cd gearmand-%s && ./configure --without-mysql --prefix=\"%s\" --with-boost=\"%s/..\" %s" % \
                (self.version, finished_package, boost_libdir, shared_flags))
        self.run("cd gearmand-%s && make %s && make %s install" % (self.version, make_options, make_options))

        if self.options.server:
            archive = "gearmand-%s/libgearman-server/.libs/libgearman-server.a" % self.version
            if self.options.shared:
                # we need to build a shared version of the server
                self.run('g++ -o "%s/lib/libgearman-server.so" -shared -rdynamic ' % finished_package +
                        ' -Wl,--whole-archive "%s" -Wl,--no-whole-archive' % archive +
                        ' %s %s' % (os.getenv("LDFLAGS") or "", os.getenv("LIBS") or ""))
            else:
                # just copy the archive
                self.run('cp "%s" "%s/lib"' % (archive, finished_package))

            # copy the relevant include files
            cp = FileCopier("%s/gearmand-%s" % (os.getcwd(), self.version), finished_package)
            cp("*.h*", dst="include/libgearman-server", src="libgearman-server")

    def package(self):
        self.copy("*", dst="lib", src="pkg/lib", links=True)
        self.copy("*", dst="bin", src="pkg/bin", links=True)
        self.copy("*", dst="sbin", src="pkg/bin", links=True)
        self.copy("*", dst="include", src="pkg/include", links=True)


    def package_info(self):
        libs = ["gearman"]
        if self.options.server:
            libs += ["gearman-server"]

        self.cpp_info.libs = libs
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]
