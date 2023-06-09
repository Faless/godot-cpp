import os, sys

from SCons.Platform import TempFileMunge


def exists(env):
    return os.name == "nt" or sys.platform == "cygwin"


# Workaround for long command lines on Windows. See:
# http://www.scons.org/wiki/LongCmdLinesOnWin32
def generate(env):
    if env.get("is_msvc", False):
        # Applied by MSVC tool.
        return

    if os.name == "nt":
        _custom_spawn(env)
    elif sys.platform == "cygwin":
        # Long line hack. Use tempfile for ar on cywin.
        _custom_arcom(env)


def _custom_arcom(env):
    env["TEMPFILE"] = TempFileMunge
    env["ARCOM"] = "${TEMPFILE('\"$AR\" $ARFLAGS $TARGET $SOURCES')}"


def _custom_spawn(env):
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

    env["SPAWN"] = mySpawn
    env.Replace(ARFLAGS=["q"])
