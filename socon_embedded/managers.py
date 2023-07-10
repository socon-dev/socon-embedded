from socon.core.management.subcommand import SubcommandManager
from socon.core.manager import BaseManager, managers
from socon.core.registry.config import RegistryConfig
from socon.core.registry import registry, projects


# ------------------------- Build subcommand manager ------------------------- #

class SubcommandBuilderManager(SubcommandManager):
    name = "build_manager"
    lookup_module = SubcommandManager.lookup_module + ".build"

    def get_modules(self, config: type[RegistryConfig]) -> list:
        modules = super().get_modules(config)
        modules.extend([
            "socon_embedded.management.commands.subcommands.from_file"
        ])
        return modules


# ------------------------------ Plugin manager ------------------------------ #


class AppManager(BaseManager):
    name = "app_manager"
    lookup_module = "apps"

    def get_modules(self, config: type[RegistryConfig]) -> list[str]:
        modules = super().get_modules(config)
        if isinstance(modules, str):
            modules = [modules]
        modules.extend(["socon_embedded.apps"])
        return modules


class BuilderManager(BaseManager):
    name = "builder"
    lookup_module = "builder"


def get_builder_manager():
    # Load the builder manager to get access to all registered builders
    # in the common config or in the current project
    builder_manager = managers.get_manager("builder")
    builder_manager.find_hooks_impl(registry.get_user_common_config())
    try:
        builder_manager.find_hooks_impl(projects.get_project_config_by_env())
    except LookupError:
        pass

    return builder_manager
