#!/usr/bin/env python

import os
import platform
import sys
import subprocess
from binding_generator import scons_generate_bindings, scons_emit_files


def add_sources(sources, dir, extension):
    for f in os.listdir(dir):
        if f.endswith("." + extension):
            sources.append(dir + "/" + f)


env = Environment()
env.Tool("godotcpp", toolpath=["tools"])
platform_tool = Tool(env["platform"], toolpath=["tools"])

if platform_tool is None or not platform_tool.exists(env):
    raise ValueError("Required toolchain not found for platform " + env["platform"])

platform_tool(env)
Help(env["options"].GenerateHelpText(env))

# Detect and print a warning listing unknown SCons variables to ease troubleshooting.
unknown = env["options"].UnknownVariables()
if unknown:
    print("WARNING: Unknown SCons variables were passed and will be ignored:")
    for item in unknown.items():
        print("    " + item[0] + "=" + item[1])

print("Building for architecture " + env["arch"] + " on platform " + env["platform"])

# Require C++17
if env.get("is_msvc", False):
    env.Append(CXXFLAGS=["/std:c++17"])
else:
    env.Append(CXXFLAGS=["-std=c++17"])

if env["target"] == "debug":
    env.Append(CPPDEFINES=["DEBUG_ENABLED", "DEBUG_METHODS_ENABLED"])

if env["float"] == "64":
    env.Append(CPPDEFINES=["REAL_T_IS_DOUBLE"])


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
if "ios_emulator" in env and env["ios_emulator"]:
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
