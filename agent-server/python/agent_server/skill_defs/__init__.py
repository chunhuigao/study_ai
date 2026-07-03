import importlib
import pkgutil

_BUILTIN_SKILLS = None


def _discover_skills():
    skills = []
    package_dir = __path__
    for module_info in pkgutil.iter_modules(package_dir):
        module = importlib.import_module(f".{module_info.name}", package=__name__)
        skill = getattr(module, "SKILL", None)
        if isinstance(skill, dict) and skill.get("id") and skill.get("name"):
            skills.append(skill)
    return skills


def get_builtin_skills():
    global _BUILTIN_SKILLS
    if _BUILTIN_SKILLS is None:
        _BUILTIN_SKILLS = _discover_skills()
    return _BUILTIN_SKILLS


def reload_builtin_skills():
    global _BUILTIN_SKILLS
    _BUILTIN_SKILLS = _discover_skills()
    return _BUILTIN_SKILLS