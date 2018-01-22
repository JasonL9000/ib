import os
import platform
import os.path
import unittest
from ib import Cfg
from ib.test import helper

def gcc_debug_subject():
  return Cfg(helper.cfgs_dir, helper.cfg_gcc_debug)

def gcc_release_subject():
  return Cfg(helper.cfgs_dir, helper.cfg_gcc_release)

def clang_debug_subject():
  return Cfg(helper.cfgs_dir, helper.cfg_clang_debug)

def clang_release_subject():
  return Cfg(helper.cfgs_dir, helper.cfg_clang_release)

class TestCfgModel(unittest.TestCase):

  def tearDown(self):
    # clean up used environment variables in case of failure
    if 'INCL_ENV_VAR' in os.environ:
      os.environ.pop('INCL_ENV_VAR', None)

  def test_exists(self):
    self.assertIsNotNone(Cfg)

  def test_constructs(self):
    cfg = gcc_debug_subject()
    self.assertIsNotNone(Cfg)

  def test_os_exposed(self):
    cfg = gcc_debug_subject()
    self.assertEqual(os, cfg.os)

  def test_platform_exposed(self):
    cfg = gcc_debug_subject()
    self.assertEqual(platform, cfg.platform)

  # cfgs/gcc_debug

  def test_cc_flags_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(
      [ '--std=c++14', '-x', 'c++', '-fPIC', '-D', 'DEBUG', '-g',
      '-DDJ_ENABLE_ABORT_IF' ],
      cfg.cc.flags
    )

  def test_cc_tool_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.cc.tool, 'gcc')

  def test_cc_incl_dirs_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.cc.incl_dirs, [])

  def test_cc_hdrs_flags_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.cc.hdrs_flags, [ '-MM', '-MG' ])

  def test_link_flags_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.link.flags, [])

  def test_link_tool_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.link.tool, 'gcc')

  def test_link_libs_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.link.libs, [ 'stdc++' ])

  def test_link_static_libs_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.link.static_libs, [])

  def test_link_lib_dirs_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.link.lib_dirs, [])

  def test_make_tool_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.make.tool, 'make')

  def test_make_flags_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.make.flags, [ '-s' ])

  def test_make_force_flag_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.make.force_flag, '-B')

  def test_make_all_pseudo_target_property_on_gcc_debug_cfg(self):
    cfg = gcc_debug_subject()
    self.assertEqual(cfg.make.all_pseudo_target, 'all')

  # cfgs/clang_debug

  def test_cc_flags_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(
      [
        '--std=c++14', '-x', 'c++', '-fPIC', '-Weverything', '-Wno-c++98-compat',
        '-Wno-shadow', '-Wno-global-constructors', '-Wno-exit-time-destructors',
        '-Wno-padded', '-Wno-weak-vtables', '-D', 'DEBUG', '-g',
        '-DDJ_ENABLE_ABORT_IF'
      ],
      cfg.cc.flags
    )

  def test_cc_tool_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.cc.tool, 'clang')

  def test_cc_incl_dirs_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.cc.incl_dirs, [])

  def test_cc_hdrs_flags_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.cc.hdrs_flags, [ '-MM', '-MG' ])

  def test_link_flags_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.link.flags, [])

  def test_link_tool_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.link.tool, 'clang')

  def test_link_libs_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.link.libs, [ 'stdc++' ])

  def test_link_static_libs_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.link.static_libs, [])

  def test_link_lib_dirs_property_on_clang_debug_cfg(self):
    cfg = clang_debug_subject()
    self.assertEqual(cfg.link.lib_dirs, [])

  # environment variable test
  def test_dynamic_environment_variable(self):
    os.environ['INCL_ENV_VAR'] = '/include/dir'
    cfg = clang_debug_subject()
    self.assertEqual(cfg.cc.incl_dirs, ['/include/dir'])

if __name__ == '__main__':
  unittest.main()
