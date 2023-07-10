from __future__ import annotations
import itertools

from typing import Dict, List, Optional, Union
from socon_embedded.builder import BuildInfo

from socon_embedded.exceptions import YamlFormatError, YamlParserError
from socon_embedded.managers import get_builder_manager
from socon_embedded.schema.tasks.task import Taskable
from socon_embedded.schema.base import Base, Nameable, get_field_names

from pydantic import BaseModel, field_validator, model_validator

from datalookup import Dataset


class AppRegistry(Base, Nameable, Taskable):
    name: Optional[str]
    vars: Optional[dict] = {}
    apps: List[AppConfig] = []

    def filter(self, filters: dict = {}, excludes: dict = {}) -> AppRegistry:
        """
        Filter using datalookup library, Return a new registry
        with the filtered apps
        """
        if filters == {} and excludes == {}:
            return self

        dataset = Dataset(self.model_dump()["apps"])

        # Filter and excludes apps
        apps = dataset.on_cascade().filter(**filters)
        if excludes:
            apps = apps.on_cascade().exclude(**excludes)

        # Re-create the AppConfig object for each filtered apps
        filtered_apps = []
        for app in apps:
            filtered_apps.append(AppConfig(**app.values()))

        # Return a new registry with the filtered apps
        return AppRegistry(
            **self.model_dump(exclude="apps"),
            apps=filtered_apps
        )

    def _get_app(self, name: str) -> Optional[AppConfig]:
        """Get an application from the registry"""
        for app in self.apps:
            if name == app.name:
                return app
        return None

    def add_application(self, name: str, group: list = []) -> AppConfig:
        app = self._get_app(name)
        if app is None:
            app = AppConfig(name=name, group=group)
            self.apps.append(app)
        else:
            app.add_group(group)
        return app

    def add_vars(self, **variables):
        """Add global variable to the registry"""
        self.vars |= variables


class AppConfig(Base, Nameable, Taskable):
    builders: List[AppBuilder] = []
    group: Optional[Union[str, int, list]] = None
    variants: Optional[List[Variant]] = []

    @field_validator("group", mode="before")
    @classmethod
    def convert_group_to_list(cls, v: Union[str, int, list]):
        if isinstance(v, (str, int)):
            return [v]
        return v

    @model_validator(mode="after")
    def validate_builder_exist(self):
        # Find common builders and project builders if the project define
        builder_manager = get_builder_manager()

        not_existing_builders = []
        for builder in self.builders:
            if builder.name not in builder_manager.get_hooks_name():
                not_existing_builders.append(builder.name)

        if not_existing_builders:
            raise YamlParserError(
                "Following builder(s) does not exist(s):\n"
                f"{not_existing_builders}"
            )

        return self

    @model_validator(mode="after")
    def validate_builder_ref(self):
        builders = [builder.name for builder in self.builders]
        for variant in self.variants:
            builder_refs = [ref for builder in variant.builders for ref in builder.ref]
            for ref in builder_refs:
                if ref not in builders:
                    raise YamlFormatError(
                        f"Reference to '{ref}' builder does not exist.\n"
                        f"Please check following variant:\n{variant}"
                    )
        return self

    @staticmethod
    def _get_build_configs(app: str, builder: AppBuilder) -> list[BuildConfig]:
        build_configs = []

        # If the user specified the configs entry, we need to create
        # multiple build configuration
        if builder.variant_args:
            keys, values = zip(*builder.variant_args.items())
            permutations_dicts = [
                dict(zip(keys, v)) for v in itertools.product(*values)
            ]
            for variant in permutations_dicts:
                # Create a new builder
                config_builder = AppBuilder(
                    **builder.model_dump(exclude="variant_args"), variant_args=variant
                )
                build_configs.append(
                    BuildConfig(app=app, builder=config_builder)
                )
        else:
            build_configs.append(
                BuildConfig(app=app, builder=builder)
            )

        return build_configs

    def get_build_configs(self) -> List[BuildConfig]:
        build_configs = []
        builders_ref: Dict[str, AppBuilder] = {}

        for builder in self.builders:
            # Save the builder reference for the variant
            if builder.name not in builders_ref:
                builders_ref[builder.name] = builder

            # If the user specified the configs entry, we need to create
            # multiple build configuration
            build_configs.extend(self._get_build_configs(self.name, builder))

        for variant in self.variants:
            app = self.name + f".{variant.name}"
            for vbuilder in variant.builders:
                for ref in vbuilder.ref:
                    builder_ref = builders_ref[ref]
                    builder = builder_ref.merge_variant_builder(vbuilder)
                    build_configs.extend(
                        self._get_build_configs(app, builder)
                    )

        return build_configs

    def _get_builder(self, name: str) -> Optional[AppBuilder]:
        for builder in self.builders:
            if name == builder.name:
                return builder
        return None

    def add_group(self, value: str) -> None:
        """Add a value to the application config group"""
        if not self.group:
            self.group = [value]
        elif value not in self.group:
            self.group.append(value)

    def add_builder(self, name: str, project_file: str, extras_options: dict = None):
        """Add a builder to the application"""
        builder = self._get_builder(name)
        if builder is None:
            builder = AppBuilder(
                name=name, project_file=project_file, variant_args=extras_options
            )
            self.builders.append(builder)
        return builder


class BuildConfig(Base, Taskable):
    app: str
    builder: AppBuilder

    def get_buildinfo(self) -> dict:
        return {
            "app": self.app,
            **self.builder.model_dump(
                by_alias=True,
                exclude=[
                    *get_field_names(Taskable),
                    *get_field_names(Nameable)
                ]
            )
        }

    def create_buildinfo(self) -> BuildInfo:
        build_info = self.get_buildinfo()
        build_info.pop("raw_args")
        return BuildInfo(
            builder=self.builder.name,
            **build_info
        )


class Builder(Taskable):
    variant_args: Optional[Dict[str, Union[str, list]]] = {}
    raw_args: Optional[list] = []


class AppBuilder(Base, Builder, Nameable):
    project_file: str

    def merge_variant_builder(self, other: VariantBuilder) -> AppBuilder:
        """Merge a builder with a variant builder"""
        builder = self.model_copy(deep=True)

        # Merge tasks from other to the current builder
        builder.merge_tasks(other, other.keep_tasks, "tasks")
        builder.merge_tasks(other, other.keep_post_tasks, "post_tasks")

        # Merge all remaining fields
        builder_dict = builder.model_dump() | other.model_dump(
            exclude=[
                *get_field_names(Taskable),
                *get_field_names(VariantBuilderField)
            ]
        )

        return AppBuilder(**builder_dict)


class VariantBuilderField(BaseModel):
    ref: Union[str, list]
    keep_tasks: Optional[bool] = False
    keep_post_tasks: Optional[bool] = False

    @field_validator("ref", mode="before")
    @classmethod
    def convert_ref_to_list(cls, v: Union[str, list]):
        if isinstance(v, str):
            return [v]
        return v


class VariantBuilder(Builder, VariantBuilderField):
    pass


class Variant(Base, Nameable, Taskable):
    group: Optional[Union[str, int, list]] = None
    builders: Optional[List[VariantBuilder]] = []
