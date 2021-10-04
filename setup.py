from setuptools import setup

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        printf("RUNNING POST INSTALL COMMANDS")

setup(cmdclass={
    "install": PostInstallCommand,
})