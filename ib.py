#!/usr/bin/python

# Copyright Jason Lucas
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse, ast, os, platform, subprocess, tempfile, textwrap


class IbError(Exception): pass


def GetExt(path):
  _, ext = os.path.splitext(path)
  return ext


def ReplaceExt(path, new_ext):
  head, _ = os.path.splitext(path)
  return head + new_ext


def YieldSubtypes(base_type):
  for obj in globals().itervalues():
    if type(obj) is type and issubclass(obj, base_type) and obj is not base_type:
      yield obj


# -----------------------------------------------------------------------------


class Rule(object):
  def __init__(self, outputs):
    super(Rule, self).__init__()
    self.outputs = outputs
    self.dependencies = set()
    self.recipe_lines = []
    self.show_progress = 0
    self.recipe_action = 'Building'
    for output in outputs:
      dirname = os.path.dirname(output)
      if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

  @property
  def script(self):
    progress_recipe = ''
    if self.show_progress:
      if len(self.recipe_lines) > 0:
        progress_recipe = '\t@$(SHOW_PROGRESS) %s $@\n' % self.recipe_action
      else:
        progress_recipe = '\t@$(SHOW_PROGRESS) %s done\n' % self.recipe_action

    return '%s:%s\n%s\n' % (
        ' '.join(self.outputs),
        ''.join(' \\\n%s' % dependency for dependency in self.dependencies),
        progress_recipe + '\n'.join('\t%s' % line for line in self.recipe_lines))

  def AppendToRecipe(self, args):
    self.recipe_lines.append(' '.join(args))


# -----------------------------------------------------------------------------


class Spec(object):
  def __init__(self, branch, atom, ext):
    super(Spec, self).__init__()
    self.branch = branch
    self.atom = atom
    self.ext = ext

  def __repr__(self):
    return '%s(branch=%r, atom=%r, ext=%r)' % (self.__class__.name, self.branch, self.atom, self.ext)

  def __eq__(self, other):
    return (
        self.atom == other.atom and
        self.branch == other.branch and
        self.ext == other.ext)

  def __hash__(self):
    return hash((self.atom, self.branch, self.ext))

  @property
  def relpath(self):
    return os.path.join(self.branch, type(self).PREFIX + self.atom) + self.ext

  def YieldImpliedSpecs(self, planner, abspath):
    return []

  @classmethod
  def ConvBaseToAtom(cls, base):
    return base[len(cls.PREFIX):]

  @classmethod
  def YieldExts(cls):
    yield cls.DEFAULT_EXT
    for ext in cls.OTHER_EXTS:
      yield ext


class CppSpec(Spec):
  def __init__(self, *args, **kwargs):
    super(CppSpec, self).__init__(*args, **kwargs)
    self.cached_hdrs = None

  def YieldImpliedSpecs(self, planner, abspath):
    for hdr in planner.GetHdrs(abspath):
      implementation_spec = GetDefaultRelatedSpec(hdr, ObjSpec)
      if planner.GetPlan(implementation_spec).doable:
        yield implementation_spec

  PREFIX = ''
  DEFAULT_EXT = '.cc'
  OTHER_EXTS = [ '.c', '.cpp', '.cxx' ]


class ExeSpec(Spec):
  def __init__(self, *args, **kwargs):
    super(ExeSpec, self).__init__(*args, **kwargs)

  PREFIX = ''
  DEFAULT_EXT = ''
  OTHER_EXTS = [ '.js', '.exe' ]


class SoSpec(Spec):
  def __init__(self, *args, **kwargs):
    super(SoSpec, self).__init__(*args, **kwargs)

  PREFIX = ''
  DEFAULT_EXT = '.so'
  OTHER_EXTS = []


class HdrSpec(Spec):
  def __init__(self, *args, **kwargs):
    super(HdrSpec, self).__init__(*args, **kwargs)

  PREFIX = ''
  DEFAULT_EXT = '.h'
  OTHER_EXTS = [ '.hpp', '.hh', '.hxx', '.inl' ]


class ObjSpec(Spec):
  def __init__(self, *args, **kwargs):
    super(ObjSpec, self).__init__(*args, **kwargs)

  PREFIX = ''
  DEFAULT_EXT = '.o'
  OTHER_EXTS = []


def GetDefaultRelatedSpec(old_spec, new_type):
  return new_type(old_spec.branch, old_spec.atom, new_type.DEFAULT_EXT)


def GetSpecTypeByExt(ext):
  type = _SPEC_TYPE_BY_EXT.get(ext)
  if type is None:
    raise IbError("unknown extension %r" % ext)
  return type


def YieldRelatedSpecs(old_spec, new_type):
  for ext in new_type.YieldExts():
    yield new_type(old_spec.branch, old_spec.atom, ext)


def _InitSpecTypes():
  global _SPEC_TYPE_BY_EXT
  _SPEC_TYPE_BY_EXT = {}
  for spec_type in YieldSubtypes(Spec):
    for ext in spec_type.YieldExts():
      if _SPEC_TYPE_BY_EXT.setdefault(ext, spec_type) is not spec_type:
        raise ValueError("extension %r is ambiguous" % ext)


_InitSpecTypes()


# -----------------------------------------------------------------------------


class Job(object):
  def __init__(self, input_spec):
    super(Job, self).__init__()
    self.input_spec = input_spec
    self.explicit_output_specs = {}

  @property
  def desc(self):
    return '%s %s -> %s' % (
        type(self).VERB,
        self.input_spec.relpath,
        ', '.join(self.GetOutputSpec(key).relpath
                  for key in type(self).OUTPUT_SPEC_TYPES.iterkeys()))

  def GetOutputSpec(self, key):
    return self.explicit_output_specs.get(
        key,
        GetDefaultRelatedSpec(
            self.input_spec, type(self).OUTPUT_SPEC_TYPES[key]))

  def SetOutputSpec(self, key, output_spec):
    if self.explicit_output_specs.setdefault(key, output_spec) != output_spec:
      raise IbError("%s: cannot replace %s output with %s" % (
          self.desc, key, output_spec.relpath))

  def GetRule(self, planner):
    return Rule(
      [ planner.GetPlan(self.GetOutputSpec(key)).GetOutputAbspath(planner)
        for key in type(self).OUTPUT_SPEC_TYPES ])


class CompilerJob(Job):
  def __init__(self, *args, **kwargs):
    super(CompilerJob, self).__init__(*args, **kwargs)

  def GetRule(self, planner):
    rule = super(CompilerJob, self).GetRule(planner)
    rule.recipe_action = 'Compiling';
    input_abspath = planner.GetPlan(self.input_spec).GetOutputAbspath(planner)
    rule.dependencies.add(input_abspath)
    for hdr in planner.GetHdrs(input_abspath):
      plan = planner.GetPlan(hdr)
      if plan.doable:
        rule.dependencies.add(plan.GetOutputAbspath(planner))
    rule.AppendToRecipe(
        planner.GetCcArgs() + [ '-c', '-o ' + rule.outputs[0], input_abspath ])
    return rule

  VERB = 'compile'
  INPUT_SPEC_TYPE = CppSpec
  OUTPUT_SPEC_TYPES = { 'obj': ObjSpec }


class LinkerJob(Job):
  def __init__(self, *args, **kwargs):
    super(LinkerJob, self).__init__(*args, **kwargs)

  @property
  def extra_link_opts(self):
    return []

  def GetRule(self, planner):
    plans = set()
    planner.GetPlan(self.input_spec).ExtendPlans(planner, plans)
    rule = super(LinkerJob, self).GetRule(planner)
    rule.recipe_action = 'Linking';
    out_flag_prefix = planner.cfg.link.out_flag_prefix if hasattr(planner.cfg.link, 'out_flag_prefix') else '-o '
    lib_flag_prefix = planner.cfg.link.lib_flag_prefix if hasattr(planner.cfg.link, 'lib_flag_prefix') else '-l'
    for plan in plans:
      if type(plan.output_spec) is ObjSpec:
        rule.dependencies.add(plan.GetOutputAbspath(planner))
    rule.AppendToRecipe(
        [ planner.cfg.link.tool ] +
        self.extra_link_opts +
        planner.cfg.link.flags +
        [ out_flag_prefix + rule.outputs[0] ] + list(rule.dependencies) +
        [ '-L' + lib_dir for lib_dir in planner.cfg.link.lib_dirs ] +
        [ lib_flag_prefix + lib for lib in planner.cfg.link.libs ] +
        ([ '-Wl,-Bstatic' ] if platform.system() != 'Darwin' and platform.system() != 'Windows' else []) +
        [ '-l' + lib for lib in planner.cfg.link.static_libs ] +
        ([ '-Wl,-Bdynamic' ] if platform.system() != 'Darwin' and platform.system() != 'Windows' else []))
    return rule

  VERB = 'link'
  INPUT_SPEC_TYPE = ObjSpec


class ExeJob(LinkerJob):
  def __init__(self, *args, **kwargs):
    super(ExeJob, self).__init__(*args, **kwargs)

  def GetRule(self, planner):
    rule = super(ExeJob, self).GetRule(planner)
    # This is a temporary work-around for -main executables.
    # It should really backtrack from foo-main to foo-main.o properly.
    if rule.outputs[0].endswith("-main"):
      rule.AppendToRecipe([ "mv", rule.outputs[0], rule.outputs[0][:-5] ])
    return rule

  OUTPUT_SPEC_TYPES = { 'exe': ExeSpec }


class SoJob(LinkerJob):
  def __init__(self, *args, **kwargs):
    super(SoJob, self).__init__(*args, **kwargs)

  @property
  def extra_link_opts(self):
    return [ '-shared', '-rdynamic' ]

  OUTPUT_SPEC_TYPES = { 'so': SoSpec }


class Producer(object):
  def __init__(self, key, job_type):
    super(Producer, self).__init__()
    self.key = key
    self.job_type = job_type

  def YieldJobs(self, planner, output_spec):
    for input_spec in YieldRelatedSpecs(output_spec, self.job_type.INPUT_SPEC_TYPE):
      job = planner.GetJob(self.job_type, input_spec)
      job.SetOutputSpec(self.key, output_spec)
      yield job


def GetProducersByOutputSpecType(spec_type):
  return _PRODUCERS_BY_OUTPUT_SPEC_TYPE.get(spec_type, [])


def _InitJobTypes():
  global _PRODUCERS_BY_OUTPUT_SPEC_TYPE
  _PRODUCERS_BY_OUTPUT_SPEC_TYPE = {}
  for job_type in YieldSubtypes(Job):
    if not hasattr(job_type, 'OUTPUT_SPEC_TYPES'):
      continue
    for key, spec_type in job_type.OUTPUT_SPEC_TYPES.iteritems():
      _PRODUCERS_BY_OUTPUT_SPEC_TYPE.setdefault(spec_type, []).append(Producer(key, job_type))


_InitJobTypes()


# -----------------------------------------------------------------------------


class Plan(object):
  def __init__(self):
    super(Plan, self).__init__()

  @property
  def understood(self):
    return True

  def ExtendPlans(self, planner, plans):
    if self not in plans:
      plans.add(self)
      for implied_spec in self.YieldImpliedSpecs(planner):
        planner.GetPlan(implied_spec).ExtendPlans(planner, plans)
      if self.input_spec is not None:
        planner.GetPlan(self.input_spec).ExtendPlans(planner, plans)

  def YieldImpliedSpecs(self, planner):
    for implied_spec in self.output_spec.YieldImpliedSpecs(planner, self.GetOutputAbspath(planner)):
      yield implied_spec


class DoablePlan(Plan):
  def __init__(self):
    super(DoablePlan, self).__init__()

  @property
  def doable(self):
    return True


class JobPlan(DoablePlan):
  def __init__(self, key, job):
    super(JobPlan, self).__init__()
    self.key = key
    self.job = job

  @property
  def desc(self):
    return self.job.desc

  @property
  def input_spec(self):
    return self.job.input_spec

  @property
  def output_spec(self):
    return self.job.GetOutputSpec(self.key)

  def GetDepth(self, planner):
    return planner.GetPlan(self.job.input_spec).GetDepth(planner) + 1

  def GetOutputAbspath(self, planner):
    return os.path.join(planner.out_root, self.output_spec.relpath)

  def IsReady(self, planner):
    return planner.IsMade(self.input_spec)


class SrcPlan(DoablePlan):
  def __init__(self, output_spec):
    super(SrcPlan, self).__init__()
    self.output_spec = output_spec

  @property
  def desc(self):
    return 'source'

  @property
  def input_spec(self):
    return None

  @property
  def job(self):
    return None

  def GetOutputAbspath(self, planner):
    return os.path.join(planner.src_root, self.output_spec.relpath)

  def IsReady(self, planner):
    return True


class UndoablePlan(Plan):
  def __init__(self):
    super(UndoablePlan, self).__init__()

  @property
  def doable(self):
    return False


class AmbiguousPlan(UndoablePlan):
  def __init__(self, plans):
    super(AmbiguousPlan, self).__init__()
    self.plans = plans

  @property
  def desc(self):
    return 'ambiguous plan'

  @property
  def output_spec(self):
    return self.plans[0].output_spec


class NoPlan(UndoablePlan):
  def __init__(self, output_spec):
    super(NoPlan, self).__init__()
    self.output_spec = output_spec

  @property
  def desc(self):
    return 'no plan'

  @property
  def understood(self):
    return False


# -----------------------------------------------------------------------------


class Planner(object):
  def __init__(self, cfg, src_root, out_root, cwd=os.getcwd()):
    self.cfg = cfg
    self.src_root = src_root
    self.out_root = out_root
    self.branch = self.TryConvAbspathToRelpath(cwd)
    self.cached_jobs = {}
    self.cached_plans = {}
    self.cached_hdrs = {}
    self.made_specs = set()

  def ConvAbspathToRelpath(self, abspath):
    relpath = self.TryConvAbspathToRelpath(abspath)
    if relpath is None:
      raise IbError(
          "The file %r is not in the source tree or the output tree "
          "so I can't compute a relative path for it." % abspath)
    return relpath

  def ConvAbspathToSpec(self, abspath):
    return self.ConvRelpathToSpec(self.ConvAbspathToRelpath(abspath))

  def ConvRelpathToSpec(self, relpath):
    branch, name = os.path.split(relpath)
    base, ext = os.path.splitext(name)
    spec_type = GetSpecTypeByExt(ext)
    return spec_type(branch, spec_type.ConvBaseToAtom(base), ext)

  def ConvTargetToRelpath(self, target):
    if target.startswith('/'):
      relpath = target[1:]
    elif self.branch is not None:
      relpath = os.path.join(self.branch, target)
    else:
      raise IbError(
          "You are trying to build the relative spec %r; however, your "
          "current directory is not under the source tree or the output "
          "tree, so I'm not sure how to resolve the relative path." % target)
    return self.ConvAbspathToRelpath(os.path.join(self.src_root, relpath))

  def ConvTargetToSpec(self, target):
    return self.ConvRelpathToSpec(self.ConvTargetToRelpath(target))

  def ConvWaveToScript(self, wave, show_progress):
    rules = [ job.GetRule(self) for job in wave ]
    all_rule = Rule([ self.cfg.make.all_pseudo_target ])
    for rule in rules:
      all_rule.dependencies |= set(rule.outputs)
      all_rule.recipe_action = rule.recipe_action
      all_rule.show_progress = show_progress;
      rule.show_progress     = show_progress;
    rules.insert(0, all_rule)

    progress_preamble = ''
    if show_progress:
      progress_preamble += 'ifndef SHOW_PROGRESS\n'
      progress_preamble += 'T := $(shell $(MAKE) ' + self.cfg.make.all_pseudo_target + ' --no-print-directory -nrRf $(firstword $(MAKEFILE_LIST)) SHOW_PROGRESS="PROGRESS_IND" | grep -c "PROGRESS_IND")\n'
      progress_preamble += 'N := x\n'
      progress_preamble += 'C = $(words $N)$(eval N := x $N)\n'
      progress_preamble += 'SHOW_PROGRESS = printf \'[%3d%%] %s %s\\n\' `expr $C \'*\' 100 / $T`\n'
      progress_preamble += 'endif\n';
      progress_preamble += '\n';

    return progress_preamble + '\n'.join(rule.script for rule in rules)

  def GetCcArgs(self):
    return [ self.cfg.cc.tool, '-I' + self.src_root, '-I' + self.out_root ]  \
        + [ '-I' + incl_dir for incl_dir in self.cfg.cc.incl_dirs ]  \
        + [ '-DIB_SRC_ROOT=' + self.src_root,
            '-DIB_OUT_ROOT=' + self.out_root ]  \
        + self.cfg.cc.flags

  def GetHdrs(self, abspath):
    hdrs = self.cached_hdrs.get(abspath)
    if hdrs is None:
      spec = self.ConvAbspathToSpec(abspath)
      spec.ext += ".ib_hdrs"
      cache_path = os.path.join(self.out_root, spec.relpath)
      try:
        with open(cache_path) as f:
          for line in f:
            hdrs.append(self.ConvRelpathToSpec(line))
        self.cached_hdrs[abspath] = hdrs
      except:
        hdrs = None
    if hdrs is None:
      args = self.GetCcArgs() + self.cfg.cc.hdrs_flags + [ abspath ]
      output = subprocess.check_output(args)
      output = output.split(':', 1)[1]
      output = output.replace('\\', ' ')
      hdrs = []
      for line in output.split():
        spec = self.TryConvAbspathToSpec(line.strip())
        if spec is not None:
          hdrs.append(spec)
      hdrs = hdrs[1:]
      self.cached_hdrs[abspath] = hdrs
      cache_dir = os.path.dirname(cache_path)
      if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
      with open(cache_path, 'w') as f:
        for hdr in hdrs:
          f.write('%s\n' % hdr.relpath)
    return hdrs

  def GetJob(self, job_type, input_spec):
    key = (job_type, input_spec)
    job = self.cached_jobs.get(key)
    if job is None:
      job = job_type(input_spec)
      self.cached_jobs[key] = job
    return job

  def GetPlan(self, output_spec):
    plan = self.cached_plans.get(output_spec)
    if plan is None:
      plans = []
      if os.path.exists(os.path.join(self.src_root, output_spec.relpath)):
        plans.append(SrcPlan(output_spec))
      for producer in GetProducersByOutputSpecType(type(output_spec)):
        for job in producer.YieldJobs(self, output_spec):
          if self.GetPlan(job.input_spec).understood:
            plans.append(JobPlan(producer.key, job))
      if len(plans) == 1:
        plan = plans[0]
      elif len(plans) > 1:
        plan = AmbiguousPlan(plans)
      else:
        plan = NoPlan(output_spec)
      self.cached_plans[output_spec] = plan
    return plan

  def IsMade(self, spec):
    return spec in self.made_specs

  def RunScript(self, script, force=False):
    with tempfile.NamedTemporaryFile(delete=False) as f:
      f.write(script)
      name = f.name
    try:
      return subprocess.call(
          [ self.cfg.make.tool ] + self.cfg.make.flags +
          ([ self.cfg.make.force_flag] if force else []) +
          [ '-f' + name, self.cfg.make.all_pseudo_target ]) == 0
    finally:
      os.unlink(name)

  def TryConvAbspathToRelpath(self, abspath):
    for root in [ self.src_root, self.out_root ]:
      if abspath.startswith(root):
        return abspath[len(root) + 1:]
    return None

  def TryConvAbspathToSpec(self, abspath):
    relpath = self.TryConvAbspathToRelpath(abspath)
    return self.ConvRelpathToSpec(relpath) if relpath is not None else None

  def YieldWaves(self, output_specs):
    for spec in output_specs:
      plan = self.GetPlan(spec)
      if not plan.doable:
        raise IbError("%s is not doable: %s" % (spec.relpath, plan.desc))
    old_specs = set(output_specs)
    pending_specs = set(output_specs)
    while True:
      ready_specs = set()
      unready_specs = set()
      while pending_specs:
        new_specs = set()
        for spec in pending_specs:
          plan = self.GetPlan(spec)
          input_spec = plan.input_spec
          if input_spec is not None and input_spec not in old_specs:
            new_specs.add(input_spec)
          if plan.IsReady(self):
            ready_specs.add(spec)
            for implied_spec in plan.YieldImpliedSpecs(self):
              if implied_spec not in old_specs:
                new_specs.add(implied_spec)
          else:
            unready_specs.add(spec)
        old_specs |= new_specs
        pending_specs = new_specs
      if not ready_specs:
        if unready_specs:
          raise IbError(
              "no progress on %s" %
              ', '.join(spec.relpath for spec in unready_specs))
        break
      jobs = []
      for spec in ready_specs:
        job = self.GetPlan(spec).job
        if job is not None:
          jobs.append(job)
      if jobs:
        yield jobs
      self.made_specs |= ready_specs
      pending_specs = unready_specs


# -----------------------------------------------------------------------------


class Cfg(object):
  "A configuration object."

  def __init__(self, root, name, base=None):
    super(Cfg, self).__init__()
    self.Obj = Obj
    self.os = os
    self.platform = platform
    if base is not None:
      self.__dict__.update(base.__dict__)
    imports = self.__Update(root, name, conv_dots=base is None)
    del self.__dict__['__builtins__']
    del self.Obj
    self.cfg = Obj(name=name, base=base.cfg if base else None, imports=imports)
    for obj_name, field_names in Cfg.DEFAULT_EMPTY_LISTS.iteritems():
      obj = getattr(self, obj_name)
      for field_name in field_names:
        if not hasattr(obj, field_name):
          setattr(obj, field_name, [])

  def __repr__(self):
    def Comment(cfg, label):
      return '# %s: %s%s' % (label, cfg.name, ExpandImports(cfg.imports))
    def ExpandImports(imports):
      return ' (imports %s)' % ', '.join('%s%s' % (name, ExpandImports(nested_imports)) for name, nested_imports in imports.iteritems()) if imports else ''
    def Lines():
      cfg = self.cfg
      label = 'name'
      while cfg is not None:
        yield Comment(self.cfg, label)
        label = 'based on'
        cfg = cfg.base
      for key, val in self.__dict__.iteritems():
        if val is not self.cfg:
          yield '%s = %r' % (key, val)
    return '\n'.join(Lines())

  def Uses(self, some_name):
    def Check(cfg):
      return cfg.name == some_name or CheckImports(cfg.imports) or (Check(cfg.base) if cfg.base is not None else False)
    def CheckImports(imports):
      return any(name == some_name or CheckImports(nested_imports) for name, nested_imports in imports.iteritems())
    return Check(self.cfg)

  def __Update(self, root, name, conv_dots=True):
    filename = os.path.join(root, *(name.split('.') if conv_dots else [ name ])) + '.cfg'
    if not os.path.isfile(filename):
      raise IbError(
          "You are trying to build the %r configuration in %r; "
          "however, the file %r does not exist." % (name, root, filename))
    with open(filename) as f:
      text = f.read()
    scout = Scout()
    for stmt in ast.parse(text, filename=filename).body:
      scout.visit(stmt)
    imports = {}
    for name in scout.imports:
      imports[name] = self.__Update(root, name)
    exec compile(ast.Module(body=scout.stmts), filename, mode='exec') in self.__dict__
    return imports

  DEFAULT_EMPTY_LISTS = {
    'cc':   [ 'incl_dirs' ],
    'link': [ 'libs', 'static_libs', 'lib_dirs' ]
  }

class Obj(object):
  "A generic object made up of the keyword args passed to its initializer."

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  def __repr__(self):
    return '%s(%s)' % (Obj.__name__, ','.join('%s=%r' % item for item in self.__dict__.iteritems()))


class Scout(ast.NodeVisitor):
  "Scouts a Python AST for the nodes of use to Cfg."

  def __init__(self):
    super(Scout, self).__init__()
    self.imports = []
    self.stmts = []

  def visit_Assign(self, node):
    self.stmts.append(node)

  def visit_AugAssign(self, node):
    self.stmts.append(node)

  def visit_Import(self, node):
    for alias in node.names:
      self.imports.append(alias.name)

  def generic_visit(self, node):
    raise SyntaxError('line %d: unexpected %s' % (node.lineno, type(node).__name__))


# -----------------------------------------------------------------------------


LABEL_FILE = '__ib__'

RED = '\x1b[1;31m'
GREEN = '\x1b[1;32m'
NORMAL = '\x1b[0m'


def main():
  def GetArgs():
    src_root = os.getcwd()
    while src_root != '/':
      if os.path.exists(os.path.join(src_root, LABEL_FILE)):
        break
      src_root = os.path.dirname(src_root)
    else:
      src_root = ''
    out_root = '../out'
    cfg_root = '.'
    cfg = 'debug'
    parser = argparse.ArgumentParser(
        description="An inntuitive builder of C++ projects. Version 0.7.1.")
    parser.add_argument(
        '--src_root', default=src_root,
        help="The root of source tree. If relative, this is path is relative "
             "to the current directory. If not given, the default is set by "
             "searching upward from the current directory for the first "
             "directory containing a file called %r. The default is currently "
             " %s." % (LABEL_FILE, (repr(src_root) if src_root else 'not set')))
    parser.add_argument(
        '--out_root', default=out_root,
        help="The root of output tree. If relative, this path is relative "
             "to the root of the source tree. The default is %r." % out_root)
    parser.add_argument(
        '--cfg_root', default=cfg_root,
        help="The root of output tree. If relative, this path is relative to "
             "the root of the source tree. The default is %r." % cfg_root)
    parser.add_argument(
        '--cfg', default=cfg,
        help="The configuration to build. The default is %r." % cfg)
    parser.add_argument(
        '--print_args', action='store_true',
        help="Print the arguments to the build, including the root "
             "directory paths and the name of the configuration to be built.")
    parser.add_argument(
        '--print_cfg', action='store_true',
        help="Print the composited config object.")
    parser.add_argument(
        '--print_script', action='store_true',
        help="Print each make script before it is run.")
    parser.add_argument(
        '--show_progress', action='store_true',
        help="Print progress.")
    parser.add_argument(
        '--no_run', action='store_true',
        help="Don't actually run any make scripts. Use this option when you "
             "want to see what the build waves would contain but not actually "
             "run them.")
    parser.add_argument(
        '--force', action='store_true',
        help="Force a total rebuild by considering all targets to be out of "
             "date. Make sure to specify this option after you modify the "
             "contents of a relevant config file.")
    parser.add_argument(
        '--test', action='store_true',
        help="Run each unit test after building.")
    parser.add_argument(
        '--test_all', action='store_true',
        help="Compile and run all the tests in the given subtree.")
    parser.add_argument(
        'targets', metavar='target', nargs='*',
        help="The spec of a target you want to build. If relative, the spec "
             "is relative to the current directory. If absolute, the spec is "
             "relative to the root of the source tree. (A spec is never truly "
             "absolute.) If the current directory is not in the source tree "
             "or the output tree, then you must give only absolute specs. The "
             "target will be built in the output tree.")
    return parser.parse_args()
  def MakeAbspath(root, argpath):
    return (
        argpath if os.path.isabs(argpath) else
        os.path.abspath(os.path.join(root, argpath)))
  try:
    args = GetArgs()
    if not args.src_root:
      raise IbError(
          "The root of the source tree was not given and could not be found. "
          "You must either provide the --src_root option explicitly, or "
          "create an empty file called %r in the directory you wish to "
          "use as your source root." % LABEL_FILE)
    args.src_root = MakeAbspath(os.getcwd(), args.src_root)
    if not os.path.isdir(args.src_root):
      raise IbError(
          "You are trying to use %r as the root of the source tree; however, "
          "it either doesn't exist or is not a directory." % args.src_root)
    args.cfg_root = MakeAbspath(args.src_root, args.cfg_root)
    if not os.path.isdir(args.cfg_root):
      raise IbError(
          "You are trying to use %r as the root of the config tree; however, "
          "it either doesn't exist or is not a directory." % args.cfg_root)
    args.out_root = MakeAbspath(
        args.src_root, os.path.join(args.out_root, args.cfg))
    if args.print_args:
      for key in [ 'src_root', 'out_root', 'cfg_root', 'cfg' ]:
        print '%s = %r' % (key, getattr(args, key))
    cfg = Cfg(args.cfg_root, args.cfg)
    if args.print_cfg:
      print cfg
    planner = Planner(
        cfg=cfg,
        src_root=args.src_root,
        out_root=args.out_root)
    targets = []
    if args.test_all:
      for target in args.targets:
        for root, _, filenames in os.walk(target):
          for filename in filenames:
            if filename.endswith('-test.cc'):
              targets.append(os.path.join(root, filename[:len(filename) - 3]))
    else:
      targets = args.targets
    success = True
    specs = [ planner.ConvTargetToSpec(target) for target in targets ]
    for wave_number, wave in enumerate(planner.YieldWaves(specs), start=1):
      script = planner.ConvWaveToScript(wave, args.show_progress)
      if args.print_script:
        print '# wave %d\n%s' % (wave_number, script)
      if args.no_run:
        return 0
      if not planner.RunScript(script, force=args.force):
        success = False
        break
    if success and (args.test_all or args.test):
      pass_specs = []
      fail_specs = []
      for spec in [ spec for spec in specs if spec.atom.endswith('-test') ]:
        print 'running %s' % spec.relpath
        status = subprocess.call(
            [ os.path.join(planner.out_root, spec.relpath) ])
        (pass_specs if status == 0 else fail_specs).append(spec)
      for name, specs in [
          (GREEN + 'passed' + NORMAL, pass_specs),
          (RED + 'failed' + NORMAL, fail_specs) ]:
        if specs:
          print '%s %d (%s)' % (
              name, len(specs), ', '.join(spec.relpath for spec in specs))
      success = not fail_specs
    return 0 if success else -1
  except IbError, err:
    print '** ib error **'
    for line in textwrap.wrap(str(err)):
      print '  ' + line
    return -1
  except subprocess.CalledProcessError, err:
    print ('*** error running subprocess ***\n%s\n%s\nreturn code: %d' %
        (err.cmd, err.output, err.returncode))


if __name__ == '__main__':
  exit(main())
