import socon

from socon.conf import global_settings


def pytest_configure(config):
    from socon.conf import settings

    settings.configure(
        default_settings=global_settings,
        INSTALLED_PLUGINS=("socon_embedded",),
        INSTALLED_PROJECTS=("projects.test_project",),
    )

    socon.setup()
