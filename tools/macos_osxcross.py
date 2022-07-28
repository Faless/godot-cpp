import os

from SCons.Script import ARGUMENTS


def options(opts):
    opts.Add("osxcross_sdk", "OSXCross SDK version", "darwin16")
    opts.Add("OSXCROSS_ROOT", "OSXCross root folder", os.environ.get("OSXCROSS_ROOT", None))


def exists(env):
    return "OSXCROSS_ROOT" in os.environ or "OSXCROSS_ROOT" in ARGUMENTS


def generate(env):
    if "OSXCROSS_ROOT" not in env:
        raise ValueError("To cross compile for iOS and macOS, the OSXCross toolchain is required, and OSXCROSS_ROOT must be set.")

    root = env["OSXCROSS_ROOT"]
    if env["arch"] == "arm64":
        basecmd = root + "/target/bin/arm64-apple-" + env["osxcross_sdk"] + "-"
    else:
        basecmd = root + "/target/bin/x86_64-apple-" + env["osxcross_sdk"] + "-"

    env["CC"] = basecmd + "clang"
    env["CXX"] = basecmd + "clang++"
    env["AR"] = basecmd + "ar"
    env["RANLIB"] = basecmd + "ranlib"
    env["AS"] = basecmd + "as"

    binpath = os.path.join(root, "target", "bin")
    if binpath not in env["ENV"]["PATH"]:
        # Add OSXCROSS bin folder to PATH (required for linking).
        env["ENV"]["PATH"] = "%s:%s" % (binpath, env["ENV"]["PATH"])
