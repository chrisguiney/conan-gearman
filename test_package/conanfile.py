from conans import ConanFile, CMake
import os


channel = os.getenv("CONAN_CHANNEL", "stable")
username = os.getenv("CONAN_USERNAME", "kmaragon")


class GearmanTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    requires = "Gearman/1.1.17@%s/%s" % (username, channel)
    generators = "cmake"

    def configure(self):
        self.options['Gearman'].shared = True
        self.options['Gearman'].server = True
        self.options['Gearman'].with_mysql = False
        self.options['libevent'].with_openssl = False

    def build(self):
        cmake = CMake(self)
        # Current dir is "test_package/build/<build_id>" and CMakeLists.txt is in "test_package"
        cmake.configure(source_dir=self.conanfile_directory, build_dir="./")
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib*", dst="bin", src="lib")

    def test(self):
        os.chdir("bin")
        self.run(".%sexample" % os.sep)
