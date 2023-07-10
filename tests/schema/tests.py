from typing import Any

from socon_embedded.schema.apps import AppConfig, AppRegistry


class TestSchemaCreation:

    def _validate(self, obj: Any):
        AppRegistry.model_validate(obj)

    def test_no_apps_registry(self):
        """Create a simple registry without any apps"""
        registry = AppRegistry(name="reg")
        assert registry.apps == []

    def test_add_app_to_registry(self):
        """Test that we can add an application to the registry after it's creation"""
        registry = AppRegistry(name="reg")
        registry.add_application("foo")
        assert len(registry.apps) == 1
        self._validate(registry)

    def test_add_group_to_an_existing_app(self):
        """
        Test that the same application will not be created twice and that we will
        only add the missing group
        """
        registry = AppRegistry(name="reg")
        app = registry.add_application("foo", group=1)
        assert app.group == [1]
        app = registry.add_application("foo", group=2)
        assert len(registry.apps) == 1
        assert app.group == [1, 2]
        self._validate(registry)

    def test_get_appication_in_registry(self):
        """Check the internal get application method"""
        app = AppConfig(name="foo")
        registry = AppRegistry(name="reg", apps=[app])
        assert registry._get_app("foo") == app

    def test_add_builder_to_app(self):
        """Check that we can add a builder to an application. Check also that
        creating twice the same builder will only add one (the first one)"""
        registry = AppRegistry(name="reg")
        app = registry.add_application("foo")
        app.add_builder("gcc", "path/to/file")
        assert len(app.builders) == 1

        # Do the same thing twice to check that we do not create two =
        # exact same builders
        app.add_builder("gcc", "path/to/file")
        assert len(app.builders) == 1

        # Vaidate the global model
        self._validate(registry)
