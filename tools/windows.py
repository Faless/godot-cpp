import sys

import long_line_fix

from SCons.Tool import msvc
from SCons.Variables import *


is_windows = sys.platform in ["win32", "msys", "cygwin"]


def options(opts):
    opts.Add(BoolVariable("use_mingw", "Use the MinGW compiler instead of MSVC - only effective on Windows", False))
    opts.Add(BoolVariable("use_clang_cl", "Use the clang driver instead of MSVC - only effective on Windows", False))


def exists(env):
    return True


def generate(env):
    base = None
    if is_windows and not env["use_mingw"] and msvc.exists(env):
        if env["arch"] == "x86_64":
            env["TARGET_ARCH"] = "amd64"
        elif env["arch"] == "x86_32":
            env["TARGET_ARCH"] = "x86"
        env["is_msvc"] = True

        # MSVC, linker, and archiver.
        msvc.generate(env)
        env.Tool("mslib")
        env.Tool("mslink")

        env.Append(CPPDEFINES=["TYPED_METHOD_BIND", "NOMINMAX"])
        env.Append(CCFLAGS=["/EHsc"])
        env.Append(LINKFLAGS=["/WX"])

        if env["use_clang_cl"]:
            env["CC"] = "clang-cl"
            env["CXX"] = "clang-cl"

    else:
        # Cross-compilation using MinGW
        env["use_mingw"] = True

        prefix = "i686" if env["arch"] == "x86_32" else env["arch"]
        env["CXX"] = prefix + "-w64-mingw32-g++"
        env["CC"] = prefix + "-w64-mingw32-gcc"
        env["AR"] = prefix + "-w64-mingw32-gcc-ar"
        env["RANLIB"] = prefix + "-w64-mingw32-gcc-ranlib"
        env["LINK"] = prefix + "-w64-mingw32-g++"
        # Want dll suffix
        env["SHLIBSUFFIX"] = ".dll"

        # These options are for a release build even using target=debug
        env.Append(CCFLAGS=["-O3", "-Wwrite-strings"])
        env.Append(
            LINKFLAGS=[
                "--static",
                "-Wl,--no-undefined",
                "-static-libgcc",
                "-static-libstdc++",
            ]
        )

        if is_windows and "TEMP" in os.environ:  # Needed by at least MSYS2-MinGW.
            env["ENV"]["TEMP"] = os.environ["TEMP"]

        # Long line hack on Windows.
        # Use custom spawn, quick AR append (to avoid files with the same names to override each other).
        if long_line_fix.exists(env):
            long_line_fix.generate(env)
