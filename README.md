> I think; therefore, ib.

# ib

A build tool that automatically resolves included sources.

```
ib -h
```

### Usage

ib projects require at least one `*.cfg` config file as well as an empty `__ib__` file used to identify root directory of project. `debug.cfg` is used by default. In this example we are using clang with c++14

`/debug.cfg`

```python
# configuration is python with many
# featured removed

cc = Obj(
  tool='clang',
  flags=[ '--std=c++14' ],
  hdrs_flags=[ '-MM', '-MG' ],
  incl_dirs=[]
)

link = Obj(
  tool='clang',
  flags=[ '-pthread' ],
  libs=[ 'stdc++' ],
  static_libs=[],
  lib_dirs=[]
)

make = Obj(
  tool='make',
  flags=[],
  all_pseudo_target='all'
)
```

#### configuration options

- **cc.tool** - compiler used (clang, gcc, avr-gcc, etc.)
- **cc.flags** - flag arguments used at compile time
- **cc.incl_dirs** - add include directories

- **link.tool** - linker to used (clang, gcc, avr-gcc, etc.)
- **link.flags** - flag arguments used at compile time
- **link.libs** - link additional libraries
- **lib.lib_dirs** - add additional library directories

- **make.tool** - tool used for `make` command
- **make.flags** - flags used for make command

Create a simple hello world program.

`/hello.cc`

```
#include <iostream>

int main(int, char*[]) {
  std::cout << "Hello World!" << std::endl;
  return 0;
}
```

Your project structure should now look like the following.

- `__ib__`
- `debug.cfg`
- `hello.cc`

Compile `hello`

```
cd <project-directory>
ib hello
```

By default ib compiles `hello.cc` to a directory located 1 directory up from current working directory named `out`.

Run `hello`

```
cd <project-directory>
# prints `Hello World`
../out/debug/hello
```

### Adding Sources

Additional source files automatically resolve when included header and source file paths have the same name. We will add and use `/util/util.h` and `/util/util.cc` in `/hello.cc`.

`/util/util.h`

```
#pragma once

namespace util {
  int add(int x, int y);
}
```

`/util/util.cc`

```
include <util/util.h>

namespace util {
  int add(int x, int y) {
    return x + y;
  }
}
```

Modify `/hello.cc`

```
#include <iostream>
#include <util/util.h>

using namespace std;

int main(int, char*[]) {
  cout << "Hello World!" << endl;
  cout << "1 + 2 = " << util::add(1, 2) << endl;
  return 0;
}
```

Your project structure should now look like the following.

- `__ib__`
- `debug.cfg`
- `hello.cc`
- `util`
  - `util.h`
  - `util.cc`

Compile and run `hello`

```
cd <project-directory>
# prints `Hello World`
../out/debug/hello
```

#### Configuring with many flags

Please note that `release.cfg` and `debug.cfg` both inherit `common.cfg`. This is helpful when projects have many flags. Example configuration files are located [here](https://github.com/JasonL9000/ib/tree/master/cfgs)

#### Recipe For Windows

For some devs, windows has always been a headache for those who are not familiar with Visual Studio IDE. It is possible to use `ib` on windows computers using the following software. Have a look a `win-common.cfg`.

- Install python to the usual place on windows `C:\Python27`
- Install [Visual Studio 2017 Community](https://www.visualstudio.com/downloads/) from Microsoft website
- When installing visual studio, make sure to check the box for adding ClangC2 Toolchain
- Install [Make for windows](http://gnuwin32.sourceforge.net/packages/make.htm) From Gnu website
- Install [Git for windows](https://git-scm.com/downloads) from Git website
- Install ib to an easy to a familiar place, I used `C:\ib`
- Open the environment variables dialog by pressing windows key and typing `Environment Variables`
- Add python to your PATH variable: `C:\Python27`
- Add clang.exe to your PATH variable: `C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Tools\ClangC2\14.10.25903\bin\HostX64` This might be different on some versions of visual studio
- Add ib to your PATH variable `C:\ib`
- Open the visual studio developer command prompt, located in the start menu under Visual Studio
- Copy the win-common.cfg to your project and use it `ib --cfg win-common example.cc` :)

## Running the Tests

The easiest way to run the tests is to install docker and run it inside there.

#### If you're using docker

- Install Docker
- Execute `./scripts/run_tests_in_docker.sh`

#### If you don't want to use docker

- Install python 2 or 3
- Install pip
- Execute `./scripts/run_tests.sh`

#### If you want to watch file for changes and auto rerun tests

- Install python 2 or 3
- Install pip
- Execute `./scripts/run_tests_watcher.sh`
