from socon.core.registry.config import ProjectConfig


class TestConfig(ProjectConfig):
    name = "projects.test_project"
    settings_module = "management.config"
