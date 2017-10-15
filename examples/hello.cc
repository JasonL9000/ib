#include <iostream>
#include <examples/hello_world/hello.h>
#include <examples/hello_world/world.h>

int main(int, char*[]) {
  #ifdef DEBUG
    std::cout << "ENV: DEBUG" << std::endl;
  #else
    std::cout << "ENV: RELEASE" << std::endl;
  #endif
  std::cout << hello() << ", " << world() << std::endl;
  return 0;
}
