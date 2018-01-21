from os import path

# roots
root_dir = path.realpath(path.join(path.dirname(__file__), '..'))
cfgs_dir = path.join(root_dir, 'cfgs')
examples_dir = path.join(root_dir, 'examples')

# configs
cfg_common = path.join(cfgs_dir, 'common')
cfg_clang_debug = path.join(cfgs_dir, 'clang_debug')
cfg_clang_release = path.join(cfgs_dir, 'clang_release')
cfg_gcc_debug = path.join(cfgs_dir, 'gcc_debug')
cfg_gcc_release = path.join(cfgs_dir, 'gcc_release')

# targets
target_basic = path.join(examples_dir, 'basic')
target_hello = path.join(examples_dir, 'hello')
target_win_hello = path.join(examples_dir, 'win_hello')
