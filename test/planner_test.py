import unittest
import re
import os
from os import path
from ib import Cfg, Planner, Spec, ExeSpec, SoSpec, CompilerJob, ExeJob, SoJob
from ib import HdrSpec
from ib.test import helper

def get_gcc_debug_cfg():
  return Cfg(helper.cfgs_dir, helper.cfg_gcc_debug)

def get_planner(cfg):
  return Planner(
    cfg=cfg,
    src_root=helper.root_dir,
    out_root=helper.out_root,
    cwd=helper.root_dir)

def get_specs(planner):
  targets = [
    'examples/hello',
    'examples/basic',
    '/examples/hello.so',
    '/examples/basic.so',
  ]

  return [ planner.ConvTargetToSpec(target) for target in targets ]


class TestPlannerModel(unittest.TestCase):

  def test_exists(self):
    self.assertIsNotNone(Planner)

  def test_constructor(self):
    planner = get_planner(get_gcc_debug_cfg());
    self.assertIsNotNone(planner)

  def test_props(self):
    cfg = get_gcc_debug_cfg()
    planner = get_planner(cfg);

    self.assertEqual(planner.cfg, cfg)
    self.assertEqual(planner.src_root, helper.root_dir)
    self.assertEqual(planner.out_root, helper.out_root)
    self.assertEqual(planner.branch, '')
    self.assertEqual(planner.cached_jobs, {})
    self.assertEqual(planner.cached_plans, {})
    self.assertEqual(planner.cached_hdrs, {})
    self.assertEqual(planner.made_specs, set())

  def test_convert_target_to_relative(self):
    planner = get_planner(get_gcc_debug_cfg())
    hello_exe_path = planner.ConvTargetToRelpath('examples/hello')
    basic_exe_path = planner.ConvTargetToRelpath('examples/basic')
    hello_so_path = planner.ConvTargetToRelpath('/examples/hello.so')
    basic_so_path = planner.ConvTargetToRelpath('/examples/basic.so')
    self.assertEqual(hello_exe_path, 'examples/hello')
    self.assertEqual(basic_exe_path, 'examples/basic')
    self.assertEqual(hello_so_path, 'examples/hello.so')
    self.assertEqual(basic_so_path, 'examples/basic.so')

  def test_convert_target_to_spec(self):
    planner = get_planner(get_gcc_debug_cfg())
    hello_exe_spec = planner.ConvTargetToSpec('examples/hello')
    basic_exe_spec = planner.ConvTargetToSpec('examples/basic')
    hello_so_spec = planner.ConvTargetToSpec('/examples/hello.so')
    basic_so_spec = planner.ConvTargetToSpec('/examples/basic.so')
    assert(type(hello_exe_spec) is ExeSpec)
    assert(type(basic_exe_spec) is ExeSpec)
    assert(type(hello_so_spec) is SoSpec)
    assert(type(basic_so_spec) is SoSpec)

  def test_planner_yields_waves(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))

    self.assertEqual(len(waves), 2, 'returns correct number of waves')
    self.assertEqual(len(waves[0]), 5, 'first wave contains 5 jobs')
    self.assertEqual(len(waves[1]), 4, 'second wave contains 4 jobs')

    compiler_jobs = [job for job in waves[0] if type(job) is CompilerJob]
    so_jobs = [job for job in waves[1] if type(job) is SoJob]
    exe_jobs = [job for job in waves[1] if type(job) is ExeJob]

    self.assertEqual(len(compiler_jobs), 5, 'wave contains correct job types')
    self.assertEqual(len(so_jobs), 2, 'wave contains correct job types')
    self.assertEqual(len(exe_jobs), 2, 'wave contains correct job types')

  def test_planner_waves_can_be_printed(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))

    for job in waves[0]:
      job.Print(planner)

    for job in waves[1]:
      job.Print(planner)

  def test_planner_converts_wave_to_script(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))
    first_script = planner.ConvWaveToScript(waves[0])
    second_script = planner.ConvWaveToScript(waves[1])

    # script from first wave
    first_target = re.split('[A-z]+\:', first_script)[1]
    self.assertIn('/tmp/out/examples/basic.o', first_target)
    self.assertIn('/tmp/out/examples/hello_world/world.o', first_target)
    self.assertIn('/tmp/out/examples/hello_world/hello.o', first_target)
    self.assertIn('/tmp/out/examples/hello.o', first_target)

    # script from second wave
    second_target = re.split('[A-z]+\:', first_script)[1]
    self.assertIn('/tmp/out/examples/hello.so', second_script)
    self.assertIn('/tmp/out/examples/hello', second_script)
    self.assertIn('/tmp/out/examples/basic.so', second_script)
    self.assertIn('/tmp/out/examples/basic', second_script)

  def test_planner_runs_script(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))
    first_script = planner.ConvWaveToScript(waves[0])
    second_script = planner.ConvWaveToScript(waves[1])

    first_result = planner.RunScript(first_script)
    second_result = planner.RunScript(second_script)
    self.assertEqual(first_result, True)
    self.assertEqual(second_result, True)

  def test_get_wave_sources(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))
    sources = planner.GetWaveSources(waves)
    for dep in sorted(sources):
      print(dep)
    self.assertEqual([
      path.join(helper.root_dir, 'examples/basic.c'),
      path.join(helper.root_dir, 'examples/hello.cc'),
      path.join(helper.root_dir, 'examples/hello_world/follow_headers.cc'),
      path.join(helper.root_dir, 'examples/hello_world/follow_headers.h'),
      path.join(helper.root_dir, 'examples/hello_world/hello.cc'),
      path.join(helper.root_dir, 'examples/hello_world/hello.h'),
      path.join(helper.root_dir, 'examples/hello_world/world.cc'),
      path.join(helper.root_dir, 'examples/hello_world/world.h'),
      '/tmp/out/examples/basic.o',
      '/tmp/out/examples/hello.o',
      '/tmp/out/examples/hello_world/follow_headers.o',
      '/tmp/out/examples/hello_world/hello.o',
      '/tmp/out/examples/hello_world/world.o'
    ], sorted(sources))

  def test_wait_for_changes(self):
    planner = get_planner(get_gcc_debug_cfg())
    specs = get_specs(planner)
    waves = list(planner.YieldWaves(specs))
    invert_op = getattr(planner, "WaitForChanges", None)
    self.assertTrue(callable(invert_op))

if __name__ == '__main__':
  unittest.main()
