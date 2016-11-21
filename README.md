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

Please note that `release.cfg` and `debug.cfg` both inherit `common.cfg`. This is helpful when projects have many flags. Example configuration files are located [here](https://github.com/JasonL9000/ib)