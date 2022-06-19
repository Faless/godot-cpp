import os, sys, platform
from SCons.Script import ARGUMENTS, EnumVariable, PathVariable, BoolVariable, Tool


def exists(env):
    return True


def options(opts):
    # Try to detect the host platform automatically.
    # This is used if no `platform` argument is passed
    if sys.platform.startswith("linux"):
        default_platform = "linux"
    elif sys.platform == "darwin":
        default_platform = "osx"
    elif sys.platform == "win32" or sys.platform == "msys":
        default_platform = "windows"
    else:
        default_platform = ARGUMENTS.get("platform", "")

    platforms = ("linux", "osx", "windows", "android", "ios", "javascript")

    opts.Add(
        EnumVariable(
            "platform",
            "Target platform",
            default_platform,
            allowed_values=platforms,
            ignorecase=2,
        )
    )

    opts.Add(EnumVariable("target", "Compilation target", "debug", allowed_values=("debug", "release"), ignorecase=2))
    opts.Add(
        PathVariable(
            "headers_dir", "Path to the directory containing Godot headers", "godot-headers", PathVariable.PathIsDir
        )
    )
    opts.Add(PathVariable("custom_api_file", "Path to a custom JSON API file", None, PathVariable.PathIsFile))
    opts.Add(
        BoolVariable("generate_bindings", "Force GDExtension API bindings generation. Auto-detected by default.", False)
    )
    opts.Add(
        BoolVariable("generate_template_get_node", "Generate a template version of the Node class's get_node.", True)
    )

    opts.Add(BoolVariable("build_library", "Build the godot-cpp library.", True))
    opts.Add(EnumVariable("float", "Floating-point precision", "32", ("32", "64")))


def generate(env):
    pass
