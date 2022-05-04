#!/usr/bin/env python

import os
import sys
import subprocess

from SCons.Util import WhereIs
from SCons.Variables.BoolVariable import _text2bool

from binding_generator import scons_generate_bindings, scons_emit_files

if sys.version_info < (3,):

    def decode_utf8(x):
        return x

else:
    import codecs

    def decode_utf8(x):
        return codecs.utf_8_decode(x)[0]


# Workaround for MinGW. See:
# http://www.scons.org/wiki/LongCmdLinesOnWin32
if os.name == "nt":
    import subprocess

    def mySubProcess(cmdline, env):
        # print "SPAWNED : " + cmdline
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(
            cmdline,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            shell=False,
            env=env,
        )
        data, err = proc.communicate()
        rv = proc.wait()
        if rv:
            print("=====")
            print(err.decode("utf-8"))
            print("=====")
        return rv

    def mySpawn(sh, escape, cmd, args, env):

        newargs = " ".join(args[1:])
        cmdline = cmd + " " + newargs

        rv = 0
        if len(cmdline) > 32000 and cmd.endswith("ar"):
            cmdline = cmd + " " + args[1] + " " + args[2] + " "
            for i in range(3, len(args)):
                rv = mySubProcess(cmdline + args[i], env)
                if rv:
                    break
        else:
            rv = mySubProcess(cmdline, env)

        return rv


def add_sources(sources, dir, extension):
    for f in os.listdir(dir):
        if f.endswith("." + extension):
            sources.append(dir + "/" + f)


def is_msvc(env):
    return os.name == "nt" and (env["CC"] == "cl" if WhereIs("cl") else False)


def get_cmdline_bool(option, default):
    """We use `ARGUMENTS.get()` to check if options were manually overridden on the command line,
    and SCons' _text2bool helper to convert them to booleans, otherwise they're handled as strings.
    """
    cmdline_val = ARGUMENTS.get(option)
    if cmdline_val is not None:
        return _text2bool(cmdline_val)
    else:
        return default


# Create the environment
env = Environment(ENV=os.environ)

# Try to detect the host platform automatically.
# This is used if no `platform` argument is passed
host_platform = ""
if sys.platform.startswith("linux"):
    host_platform = "linux"
elif sys.platform.startswith("freebsd"):
    host_platform = "freebsd"
elif sys.platform == "darwin":
    host_platform = "osx"
elif sys.platform == "win32" or sys.platform == "msys":
    host_platform = "windows"
elif ARGUMENTS.get("platform", None) is None:
    raise ValueError("Could not detect platform automatically, please specify with platform=<platform>")

selected_platform = ARGUMENTS.get("platform", host_platform)
selected_arch = ARGUMENTS.get("arch", "")

# Try to detect arch when not specified
if selected_arch == "":
    import platform as pl

    if selected_platform == "windows":
        if is_msvc(env):
            if env["TARGET_ARCH"] == "amd64":
                selected_arch = "x86_64"
            elif env["TARGET_ARCH"] == "x86":
                selected_arch = "x86_32"
            else:
                selected_arch = env["TARGET_ARCH"]
        else:
            selected_arch = pl.machine()
    elif selected_platform == "linux":
        selected_arch = pl.machine()
    elif selected_platform == "osx":
        selected_arch = "universal"
    elif selected_platform == "ios":
        if get_cmdline_bool("ios_simulator", False):
            selected_arch = "universal"
        else:
            selected_arch = "arm64"
    elif selected_platform == "android":
        selected_arch = "armv7"
    elif selected_platform == "javascript":
        selected_arch = "wasm32"
    else:
        raise ValueError(
            "Could not detect architecture automatically, please specify with arch=<architecture>" % selected_platform
        )
else:
    # This makes sure to keep the session environment variables on Windows.
    # This way, you can run SCons in a Visual Studio 2017 prompt and it will find
    # all the required tools
    if selected_platform == "windows" and is_msvc(env):
        if selected_arch == "x86_64":
            env = Environment(TARGET_ARCH="amd64")
        elif selected_arch == "x86_32":
            env = Environment(TARGET_ARCH="x86")

# This ensure we get the proper environement for non-MSVC on windows.
if host_platform == "windows" and (get_cmdline_bool("use_mingw", False) or selected_platform != "windows"):
    # Don't Clone the environment. Because otherwise, SCons will pick up msvc stuff.
    if selected_platform == "windows":
        env = Environment(ENV=os.environ, tools=["mingw"])
    else:
        # Generic Posix.
        env = Environment(ENV=os.environ, tools=["cc", "c++", "ar", "link", "textfile", "zip"])

    # Long line hack. Use custom spawn, quick AR append (to avoid files with the same names to override each other).
    env["SPAWN"] = mySpawn
    env.Replace(ARFLAGS=["q"])

# Finally define build options.
opts = Variables([], ARGUMENTS)
opts.Add(
    EnumVariable(
        "platform",
        "Target platform",
        selected_platform,
        allowed_values=("linux", "freebsd", "osx", "windows", "android", "ios", "javascript"),
        ignorecase=2,
    )
)
opts.Add("arch", "Platform-dependent architecture (arm/arm64/x86/x64/mips/...)", selected_arch)
opts.Add(BoolVariable("use_llvm", "Use the LLVM compiler - only effective when targeting Linux or FreeBSD", False))
opts.Add(BoolVariable("use_mingw", "Use the MinGW compiler instead of MSVC - only effective on Windows", False))
# Must be the same setting as used for cpp_bindings
opts.Add(EnumVariable("target", "Compilation target", "debug", allowed_values=("debug", "release"), ignorecase=2))
opts.Add(
    PathVariable(
        "headers_dir", "Path to the directory containing Godot headers", "godot-headers", PathVariable.PathIsDir
    )
)
opts.Add(PathVariable("custom_api_file", "Path to a custom JSON API file", None, PathVariable.PathIsFile))
opts.Add(
    EnumVariable(
        "generate_bindings",
        "Generate GDNative API bindings",
        "auto",
        allowed_values=["yes", "no", "auto", "true"],
        ignorecase=2,
    )
)
opts.Add("macos_deployment_target", "macOS deployment target", "")
opts.Add("macos_sdk_path", "macOS SDK path", "")
opts.Add(BoolVariable("ios_simulator", "Target iOS Simulator", False))
opts.Add(
    "IPHONEPATH",
    "Path to iPhone toolchain",
    "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain",
)
opts.Add(
    "android_api_level",
    "Target Android API level",
    "",
)
opts.Add(
    "ANDROID_NDK_ROOT",
    "Path to your Android NDK installation. By default, uses ANDROID_NDK_ROOT from your defined environment variables.",
    os.environ.get("ANDROID_NDK_ROOT", None),
)
opts.Add(BoolVariable("generate_template_get_node", "Generate a template version of the Node class's get_node.", True))
opts.Add(BoolVariable("build_library", "Build the godot-cpp library.", True))
opts.Add(EnumVariable("float", "Floating-point precision", "32", ("32", "64")))

opts.Update(env)
Help(opts.GenerateHelpText(env))

# Detect and print a warning listing unknown SCons variables to ease troubleshooting.
unknown = opts.UnknownVariables()
if unknown:
    print("WARNING: Unknown SCons variables were passed and will be ignored:")
    for item in unknown.items():
        print("    " + item[0] + "=" + item[1])

# Require C++17
if env["platform"] == "windows" and is_msvc(env):
    # MSVC
    env.Append(CXXFLAGS=["/std:c++17"])
else:
    env.Append(CXXFLAGS=["-std=c++17"])

if env["target"] == "debug":
    env.Append(CPPDEFINES=["DEBUG_ENABLED", "DEBUG_METHODS_ENABLED"])

if env["float"] == "64":
    env.Append(CPPDEFINES=["REAL_T_IS_DOUBLE"])

if env["platform"] == "linux" or env["platform"] == "freebsd":
    if env["use_llvm"]:
        env["CXX"] = "clang++"

    env.Append(CCFLAGS=["-fPIC", "-Wwrite-strings"])
    env.Append(LINKFLAGS=["-Wl,-R,'$$ORIGIN'"])

    if env["target"] == "debug":
        env.Append(CCFLAGS=["-Og", "-g"])
    elif env["target"] == "release":
        env.Append(CCFLAGS=["-O3"])

    if env["arch"] == "x86_64":
        env.Append(CCFLAGS=["-m64"])
        env.Append(LINKFLAGS=["-m64"])
    elif env["arch"] == "x86_32":
        env.Append(CCFLAGS=["-m32"])
        env.Append(LINKFLAGS=["-m32"])
    else:
        print("WARNING: Unknown linux platform, machine flags not specified")
    env["SHLIBSUFFIX"] = ".so"

elif env["platform"] == "osx":
    # Use Clang on macOS by default
    env["CXX"] = "clang++"

    if env["arch"] == "universal":
        env.Append(LINKFLAGS=["-arch", "x86_64", "-arch", "arm64"])
        env.Append(CCFLAGS=["-arch", "x86_64", "-arch", "arm64"])
    elif env["arch"] in ["x86_64", "arm64"]:
        env.Append(LINKFLAGS=["-arch", env["arch"]])
        env.Append(CCFLAGS=["-arch", env["arch"]])
    else:
        raise ValueError("Unknown OSX architecture %s." % env["arch"])

    if env["macos_deployment_target"]:
        env.Append(CCFLAGS=["-mmacosx-version-min=" + env["macos_deployment_target"]])
        env.Append(LINKFLAGS=["-mmacosx-version-min=" + env["macos_deployment_target"]])

    if env["macos_sdk_path"]:
        env.Append(CCFLAGS=["-isysroot", env["macos_sdk_path"]])
        env.Append(LINKFLAGS=["-isysroot", env["macos_sdk_path"]])

    env.Append(
        LINKFLAGS=[
            "-framework",
            "Cocoa",
            "-Wl,-undefined,dynamic_lookup",
        ]
    )

    if env["target"] == "debug":
        env.Append(CCFLAGS=["-Og", "-g"])
    elif env["target"] == "release":
        env.Append(CCFLAGS=["-O3"])

elif env["platform"] == "ios":
    if env["ios_simulator"]:
        sdk_name = "iphonesimulator"
        env.Append(CCFLAGS=["-mios-simulator-version-min=10.0"])
    else:
        sdk_name = "iphoneos"
        env.Append(CCFLAGS=["-miphoneos-version-min=10.0"])

    try:
        sdk_path = decode_utf8(subprocess.check_output(["xcrun", "--sdk", sdk_name, "--show-sdk-path"]).strip())
    except (subprocess.CalledProcessError, OSError):
        raise ValueError("Failed to find SDK path while running xcrun --sdk {} --show-sdk-path.".format(sdk_name))

    compiler_path = env["IPHONEPATH"] + "/usr/bin/"
    env["ENV"]["PATH"] = env["IPHONEPATH"] + "/Developer/usr/bin/:" + env["ENV"]["PATH"]

    env["CC"] = compiler_path + "clang"
    env["CXX"] = compiler_path + "clang++"
    env["AR"] = compiler_path + "ar"
    env["RANLIB"] = compiler_path + "ranlib"
    env["SHLIBSUFFIX"] = ".dylib"

    if env["arch"] == "universal":
        if env["ios_simulator"]:
            env.Append(LINKFLAGS=["-arch", "x86_64", "-arch", "arm64"])
            env.Append(CCFLAGS=["-arch", "x86_64", "-arch", "arm64"])
        else:
            raise ValueError("Universal ios builds are only for the simulator, please specify ios_simulator=yes")
    elif env["arch"] == "arm64":
        env.Append(LINKFLAGS=["-arch", "arm64"])
        env.Append(CCFLAGS=["-arch", "arm64"])
    else:
        raise ValueError("iOS architecture not supported: %s" % env["arch"])

    env.Append(CCFLAGS=["-isysroot", sdk_path])
    env.Append(LINKFLAGS=["-isysroot", sdk_path, "-F" + sdk_path])

    if env["target"] == "debug":
        env.Append(CCFLAGS=["-Og", "-g"])
    elif env["target"] == "release":
        env.Append(CCFLAGS=["-O3"])

elif env["platform"] == "windows":
    if is_msvc(env):
        # MSVC
        env.Append(CPPDEFINES=["TYPED_METHOD_BIND"])
        env.Append(LINKFLAGS=["/WX"])
        if env["target"] == "debug":
            env.Append(CCFLAGS=["/Z7", "/Od", "/EHsc", "/D_DEBUG", "/MDd"])
        elif env["target"] == "release":
            env.Append(CCFLAGS=["/O2", "/EHsc", "/DNDEBUG", "/MD"])

    elif host_platform != "windows":
        # Cross-compilation using MinGW
        if env["arch"] == "x86_64":
            env["CXX"] = "x86_64-w64-mingw32-g++"
            env["AR"] = "x86_64-w64-mingw32-ar"
            env["RANLIB"] = "x86_64-w64-mingw32-ranlib"
            env["LINK"] = "x86_64-w64-mingw32-g++"
        elif env["arch"] == "x86_32":
            env["CXX"] = "i686-w64-mingw32-g++"
            env["AR"] = "i686-w64-mingw32-ar"
            env["RANLIB"] = "i686-w64-mingw32-ranlib"
            env["LINK"] = "i686-w64-mingw32-g++"

    # Native or cross-compilation using MinGW
    if not is_msvc(env):
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
    env["SHLIBSUFFIX"] = ".dll"

elif env["platform"] == "android":
    # Verify NDK root
    if not "ANDROID_NDK_ROOT" in env:
        raise ValueError(
            "To build for Android, ANDROID_NDK_ROOT must be defined. Please set ANDROID_NDK_ROOT to the root folder of your Android NDK installation."
        )

    # Validate architecture
    if env["arch"] not in ["armv7", "arm64", "x86_32", "x86_64"]:
        raise ValueError("Unknown android architecture %s." % env["arch"])

    # Validate API level
    api_level = 21 if env["arch"] in ["x86_64", "arm64"] else 18
    if env["android_api_level"]:
        api_level = int(env["android_api_level"])
    if env["arch"] in ["x86_64", "arm64"] and api_level < 21:
        print("WARN: 64-bit Android architectures require an API level of at least 21; setting android_api_level=21")
        env["android_api_level"] = "21"
        api_level = 21

    # Setup toolchain
    toolchain = env["ANDROID_NDK_ROOT"] + "/toolchains/llvm/prebuilt/"
    if host_platform == "windows":
        toolchain += "windows"
        import platform as pltfm

        if pltfm.machine().endswith("64"):
            toolchain += "-x86_64"
    elif host_platform == "linux":
        toolchain += "linux-x86_64"
    elif host_platform == "osx":
        toolchain += "darwin-x86_64"
    env.PrependENVPath("PATH", toolchain + "/bin")  # This does nothing half of the time, but we'll put it here anyways

    # Get architecture info
    arch_info_table = {
        "armv7": {
            "march": "armv7-a",
            "target": "armv7a-linux-androideabi",
            "tool_path": "arm-linux-androideabi",
            "compiler_path": "armv7a-linux-androideabi",
            "ccflags": ["-mfpu=neon"],
        },
        "arm64": {
            "march": "armv8-a",
            "target": "aarch64-linux-android",
            "tool_path": "aarch64-linux-android",
            "compiler_path": "aarch64-linux-android",
            "ccflags": [],
        },
        "x86_32": {
            "march": "i686",
            "target": "i686-linux-android",
            "tool_path": "i686-linux-android",
            "compiler_path": "i686-linux-android",
            "ccflags": ["-mstackrealign"],
        },
        "x86_64": {
            "march": "x86-64",
            "target": "x86_64-linux-android",
            "tool_path": "x86_64-linux-android",
            "compiler_path": "x86_64-linux-android",
            "ccflags": [],
        },
    }
    arch_info = arch_info_table[env["arch"]]

    # Setup tools
    env["CC"] = toolchain + "/bin/clang"
    env["CXX"] = toolchain + "/bin/clang++"
    env["AR"] = toolchain + "/bin/" + arch_info["tool_path"] + "-ar"
    env["SHLIBSUFFIX"] = ".so"

    env.Append(
        CCFLAGS=["--target=" + arch_info["target"] + str(api_level), "-march=" + arch_info["march"], "-fPIC"]
    )  # , '-fPIE', '-fno-addrsig', '-Oz'])
    env.Append(CCFLAGS=arch_info["ccflags"])
    env.Append(LINKFLAGS=["--target=" + arch_info["target"] + str(api_level), "-march=" + arch_info["march"]])

    if env["target"] == "debug":
        env.Append(CCFLAGS=["-Og", "-g"])
    elif env["target"] == "release":
        env.Append(CCFLAGS=["-O3"])

elif env["platform"] == "javascript":
    env["ENV"] = os.environ
    env["CC"] = "emcc"
    env["CXX"] = "em++"
    env["AR"] = "emar"
    env["RANLIB"] = "emranlib"
    env.Append(CPPFLAGS=["-s", "SIDE_MODULE=1"])
    env.Append(LINKFLAGS=["-s", "SIDE_MODULE=1"])
    env["SHOBJSUFFIX"] = ".bc"
    env["SHLIBSUFFIX"] = ".wasm"
    # Use TempFileMunge since some AR invocations are too long for cmd.exe.
    # Use POSIX-style paths, required with TempFileMunge.
    env["ARCOM_POSIX"] = env["ARCOM"].replace("$TARGET", "$TARGET.posix").replace("$SOURCES", "$SOURCES.posix")
    env["ARCOM"] = "${TEMPFILE(ARCOM_POSIX)}"

    # All intermediate files are just LLVM bitcode.
    env["OBJPREFIX"] = ""
    env["OBJSUFFIX"] = ".bc"
    env["PROGPREFIX"] = ""
    # Program() output consists of multiple files, so specify suffixes manually at builder.
    env["PROGSUFFIX"] = ""
    env["LIBPREFIX"] = "lib"
    env["LIBSUFFIX"] = ".a"
    env["LIBPREFIXES"] = ["$LIBPREFIX"]
    env["LIBSUFFIXES"] = ["$LIBSUFFIX"]
    env.Replace(SHLINKFLAGS="$LINKFLAGS")
    env.Replace(SHLINKFLAGS="$LINKFLAGS")

    if env["target"] == "debug":
        env.Append(CCFLAGS=["-O0", "-g"])
    elif env["target"] == "release":
        env.Append(CCFLAGS=["-O3"])

# Generate bindings
env.Append(BUILDERS={"GenerateBindings": Builder(action=scons_generate_bindings, emitter=scons_emit_files)})
json_api_file = ""

if "custom_api_file" in env:
    json_api_file = env["custom_api_file"]
else:
    json_api_file = os.path.join(os.getcwd(), env["headers_dir"], "extension_api.json")

bindings = env.GenerateBindings(
    env.Dir("."), [json_api_file, os.path.join(env["headers_dir"], "godot", "gdnative_interface.h")]
)

# Forces bindings regeneration.
if env["generate_bindings"]:
    AlwaysBuild(bindings)

# Includes
env.Append(CPPPATH=[[env.Dir(d) for d in [env["headers_dir"], "include", os.path.join("gen", "include")]]])

# Sources to compile
sources = []
add_sources(sources, "src", "cpp")
add_sources(sources, "src/classes", "cpp")
add_sources(sources, "src/core", "cpp")
add_sources(sources, "src/variant", "cpp")
sources.extend([f for f in bindings if str(f).endswith(".cpp")])

env["arch_suffix"] = env["arch"]
if env["platform"] == "ios" and env["ios_simulator"]:
    env["arch_suffix"] += ".simulator"

library = None
env["OBJSUFFIX"] = ".{}.{}.{}{}".format(env["platform"], env["target"], env["arch_suffix"], env["OBJSUFFIX"])
library_name = "libgodot-cpp.{}.{}.{}{}".format(env["platform"], env["target"], env["arch_suffix"], env["LIBSUFFIX"])

if env["build_library"]:
    library = env.StaticLibrary(target=env.File("bin/%s" % library_name), source=sources)
    Default(library)

env.Append(LIBPATH=[env.Dir("bin")])
env.Append(LIBS=library_name)
Return("env")
