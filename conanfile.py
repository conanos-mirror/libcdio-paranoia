from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil


class LibcdioparanoiaConan(ConanFile):
    name = "libcdio-paranoia"
    version = "10.2-0.94-2-3"
    description = "CD paranoia on top of libcdio"
    url = "https://github.com/conanos/libcdio-paranoia"
    homepage = "https://www.gnu.org/software/libcdio/"
    license = "GPL-v3.0"
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/libcdio-paranoia/archive/release-{version}.tar.gz'
        tools.get(url_.format(version=self.version.replace("-","+",2)))
        extracted_dir = self.name + "-release-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def requirements(self):
        self.requires.add("libcdio/2.0.0@conanos/stable")

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                msbuild.build("libcdio-paranoia.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))

            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"libcdio_paranoia.pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig", "libcdio_paranoia.pc"))
            lib = "-lcdio_paranoiad" if self.options.shared else "-lcdio_paranoia"
            replacements = {
                "@prefix@"                        : self.package_folder,
                "@exec_prefix@"                   : "${prefix}/bin",
                "@libdir@"                        : "${prefix}/lib",
                "@includedir@"                    : "${prefix}/include",
                "@PACKAGE_VERSION@"               : self.version,
                "-lcdio_cdda -lcdio"              : "",
                "-lcdio_paranoia"                 : lib,
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig", "libcdio_paranoia.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

