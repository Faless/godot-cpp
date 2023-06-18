import sys, subprocess

import long_line_fix

from SCons.Tool import msvc
from SCons.Variables import *


is_windows = sys.platform in ["win32", "msys", "cygwin"]


def try_cmd(test):
    try:
        out = subprocess.Popen(
            test,
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        out.communicate()
        if out.returncode == 0:
            return True
    except Exception:
        pass
    return False


def find_mingw_tool(cmd, prefixes=[]):
    for prefix in prefixes:
        if not try_cmd(prefix + cmd + " --version"):
            continue
        return prefix + cmd
    return cmd


def options(opts):
    opts.Add(BoolVariable("use_mingw", "Use the MinGW gcc compiler instead of MSVC - only effective on Windows", False))
    opts.Add(BoolVariable("use_mingw_llvm", "Use the MinGW llvm compiler instead of MSVC - only effective on Windows", False))
    opts.Add(BoolVariable("use_clang_cl", "Use the clang driver instead of MSVC - only effective on Windows", False))


def exists(env):
    return True


def generate(env):
    if env["use_mingw_llvm"]:
        env["use_mingw"] = True

    if is_windows and not env["use_mingw"] and msvc.exists(env):
        env["is_msvc"] = True

        msvc_arch_names = {
            "x86_64": "amd64",
            "x86_32": "x86",
            "arm32": "arm",
            "arm64": "arm64",
        }

        msvc_arch = msvc_arch_names.get(env["arch"], "")
        if msvc_arch == "":
            print("WARNING: Unsupported MSVC platform '%s', the resulting binary might be invalid." % env["arch"])
            msvc_arch = os.environ.get("Platform", "")

        env["TARGET_ARCH"] = msvc_arch

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

        mingw_arch_triples = {
            "x86_64": "x86_64-w64-mingw32-",
            "x86_32": "i686-w64-mingw32-",
            "arm32": "armv7-w64-mingw32-",
            "arm64": "aarch64-w64-mingw32-",
        }

        prefix = mingw_arch_triples.get(env["arch"], "")
        if env["use_mingw_llvm"]:
            tool_prefixes = [prefix + "llvm-", prefix]
            env["CC"] = prefix + "clang"
            env["CXX"] = prefix + "clang++"
            env["AR"] = find_mingw_tool("ar", tool_prefixes)
            env["AS"] = find_mingw_tool("as", tool_prefixes)
            env["RC"] = find_mingw_tool("windres", tool_prefixes)
            env["RANLIB"] = find_mingw_tool("ranlib", tool_prefixes)
            env["LINK"] = prefix + "clang++"
        else:
            tool_prefixes = [prefix + "gcc-", prefix]
            env["CC"] = prefix + "gcc"
            env["CXX"] = prefix + "g++"
            env["AR"] = find_mingw_tool("ar", tool_prefixes)
            env["AS"] = find_mingw_tool("as", tool_prefixes)
            env["RC"] = find_mingw_tool("windres", tool_prefixes)
            env["RANLIB"] = find_mingw_tool("ranlib", tool_prefixes)
            env["LINK"] = prefix + "g++"

        env["SHLIBSUFFIX"] = ".dll"
        env.Append(CCFLAGS=["-Wwrite-strings"])
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
