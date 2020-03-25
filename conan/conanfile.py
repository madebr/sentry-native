from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


CMAKELISTS_TXT = """\
cmake_minimum_required(VERSION 3.0)
project(SentryNativeConanProject)

include("${{CMAKE_BINARY_DIR}}/conanbuildinfo.cmake")
conan_basic_setup()

add_subdirectory({} sentry-native)
"""

class SentryConan(ConanFile):
    name = "sentry"
    description = "The Sentry Native SDK is an error and crash reporting client for native applications,\n" \
                  "optimized for C and C++. Sentry allows to add tags,\n" \
                  "breadcrumbs and arbitrary custom context to enrich error reports."
    topics = "conan", "sentry", "error", "crash", "reporting"
    license = "MIT"
    homepage = "https://github.com/getsentry/sentry-native"
    url = "https://github.com/getsentry/sentry-native"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backend": ["default", "none", "breakpad", "crashpad", "inproc"],
        "transport": ["default", "none", "curl", "winhttp"],
        "build_examples": [True, False],
        "build_tests": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backend": "default",
        "transport": "default",
        "build_examples": True,
        "build_tests": True,
    }

    exports_sources = "../sentry-config.cmake.in", "../CMakeLists.txt", "../include*", "../src*", "../external*", "../vendor*", "../examples*", "../tests*",
    generators = "cmake", "cmake_find_package"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _default_transport(self):
        if self.settings.os == "Windows":
            return "winhttp"
        else:
            return "curl"

    @property
    def _default_backend(self):
        if self.settings.os == "Windows" or tools.is_apple_os(self.settings.os):
            return "crashpad"
        elif self.settings.os == "Linux":
            return "breakpad"
        else:
            return "inproc"

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.options.backend == "default":
            self.options.backend = self._default_backend
        if self.options.transport == "default":
            self.options.transport = self._default_transport
        if self.options.backend == "crashpad" and not (tools.is_apple_os(self.settings.os) or self.settings.os == "Windows"):
            raise ConanInvalidConfiguration("crashpad backend is only supported on Apple and Windows")
        if self.options.backend == "breakpad" and self.settings.os != "Linux":
            raise ConanInvalidConfiguration("breakpad backend is only supported on Linux")
        elif self.settings.os == "Windows" and self.options.backend == "inproc":
            raise ConanInvalidConfiguration("inproc backend is unsupported on Windows")

    def requirements(self):
        if self.options.transport == "curl":
            self.requires("libcurl/7.69.1")

    def build(self):
        if self.in_local_cache:
            source_folder = ".."
        else:
            source_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..").replace("\\", "/")
        tools.save("conan/CMakeLists.txt", CMAKELISTS_TXT.format(source_folder))
        cmake = CMake(self)
        cmake.definitions["SENTRY_TRANSPORT"] = self.options.transport
        cmake.definitions["SENTRY_BACKEND"] = self.options.backend
        cmake.definitions["SENTRY_BUILD_EXAMPLES"] = self.options.build_examples
        cmake.definitions["SENTRY_BUILD_TESTS"] = self.options.build_tests
        cmake.definitions["SENTRY_ENABLE_INSTALL"] = True
        cmake.configure(source_folder=os.path.join(self.build_folder, "conan"))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def test(self):
        if self.options.build_tests:
            cmake = CMake()
            cmake.test()
