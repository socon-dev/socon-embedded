from __future__ import annotations

import pkgutil

from pathlib import Path

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
        modules.extend(["socon_embedded.management.commands.subcommands.from_file"])
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


def get_action_manager() -> ActionManager:
    # Load the action manager to get access to all registered actions
    # in the common config or in the current project
    manager = managers.get_manager("ActionManager")
    manager.find_all()
    return manager


class ActionManager(BaseManager):
    name = "ActionManager"
    lookup_module = "action"

    def get_modules(self, config: type[RegistryConfig]) -> list[str]:
        modules = super().get_modules(config)
        if isinstance(modules, str):
            modules = [modules]

        current_dir = Path(__file__).resolve().parent
        action_dir = Path(current_dir, "action")
        action_modules = [
            name
            for _, name, is_pkg in pkgutil.iter_modules([str(action_dir)])
            if not is_pkg and not name.startswith("_")
        ]

        # Loop over every module and get every class that are not abstract.
        # From these class we are going to get the commands that are
        # sublcalss of BaseCommand or ProjectCommand
        for action_module in action_modules:
            modules.append("socon_embedded.action.{}".format(action_module))
        return modules
