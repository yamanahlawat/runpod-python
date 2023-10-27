""" Test functions in runpod.cli.groups.project.functions module. """

import os
import unittest
from unittest.mock import patch, mock_open

from runpod.cli.groups.project.functions import(
    STARTER_TEMPLATES, create_new_project,
    launch_project, start_project_api
)

class TestCreateNewProject(unittest.TestCase):
    """ Test the create_new_project function."""

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("os.getcwd", return_value="/current/path")
    @patch("runpod.cli.groups.project.functions.copy_template_files")
    def test_create_project_folder(self, mock_copy_template_files, mock_getcwd, mock_exists, mock_makedirs): # pylint: disable=line-too-long
        """ Test that a new project folder is created if init_current_dir is False. """
        with patch("builtins.open", new_callable=mock_open):
            create_new_project("test_project", "volume_id", "3.8")
        mock_makedirs.assert_called_once_with("/current/path/test_project")
        assert mock_copy_template_files.called
        assert mock_getcwd.called
        assert mock_exists.called

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    @patch('os.getcwd', return_value='/tmp/testdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_new_project_init_current_dir(self, mock_file_open, mock_getcwd, mock_path_exists, mock_makedirs): # pylint: disable=line-too-long
        """ Test that a new project folder is not created if init_current_dir is True. """
        project_name = "test_project"
        runpod_volume_id = "12345"
        python_version = "3.9"

        create_new_project(project_name, runpod_volume_id, python_version, init_current_dir=True)
        mock_makedirs.assert_not_called()
        mock_file_open.assert_called_with('/tmp/testdir/runpod.toml', 'w', encoding="UTF-8")
        assert mock_getcwd.called
        assert mock_path_exists.called


    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("os.getcwd", return_value="/current/path")
    @patch("runpod.cli.groups.project.functions.copy_template_files")
    def test_copy_template_files(self, mock_copy_template_files, mock_getcwd, mock_exists, mock_makedirs): # pylint: disable=line-too-long
        """ Test that template files are copied to the new project folder. """
        with patch("builtins.open", new_callable=mock_open):
            create_new_project("test_project", "volume_id", "3.8")
        mock_copy_template_files.assert_called_once_with(STARTER_TEMPLATES + "/default", "/current/path/test_project") # pylint: disable=line-too-long
        assert mock_getcwd.called
        assert mock_exists.called
        assert mock_makedirs.called

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="data with <<MODEL_NAME>> placeholder") # pylint: disable=line-too-long
    def test_replace_placeholders_in_handler(self, mock_open_file, mock_exists): # pylint: disable=line-too-long
        """ Test that placeholders in handler.py are replaced if model_name is given. """
        with patch("runpod.cli.groups.project.functions.copy_template_files"):
            create_new_project("test_project", "volume_id", "3.8", model_name="my_model")
        # mock_open_file().write.assert_called_with("data with my_model placeholder")
        assert mock_open_file.called
        assert mock_exists.called


    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock_open)
    def test_create_runpod_toml(self, mock_open_file, mock_exists):
        """ Test that runpod.toml configuration file is created. """
        with patch("runpod.cli.groups.project.functions.copy_template_files"):
            create_new_project("test_project", "volume_id", "3.8")
        toml_file_location = os.path.join(os.getcwd(), "test_project", "runpod.toml")
        mock_open_file.assert_called_once_with(toml_file_location, 'w', encoding="UTF-8") # pylint: disable=line-too-long
        assert mock_exists.called

class TestLaunchProject(unittest.TestCase):
    """ Test the launch_project function. """

    @patch('runpod.cli.groups.project.functions.load_project_config')
    @patch('runpod.cli.groups.project.functions.get_project_pod')
    @patch('runpod.cli.groups.project.functions.attempt_pod_launch')
    @patch('runpod.cli.groups.project.functions.get_pod')
    @patch('runpod.cli.groups.project.functions.SSHConnection')
    @patch('os.getcwd', return_value='/current/path')
    def test_launch_project_successfully(self, mock_getcwd, mock_ssh_connection, mock_get_pod, mock_attempt_pod_launch, mock_get_project_pod, mock_load_project_config): # pylint: disable=line-too-long
        """ Test that a project is launched successfully. """
        mock_load_project_config.return_value = {
            'project': {
                'uuid': '123456',
                'name': 'test_project',
                'volume_mount_path': '/mount/path',
                'env_vars': {'ENV_VAR': 'value'},
                'gpu': 'NVIDIA GPU'
            },
            'runtime': {
                'python_version': '3.8',
                'requirements_path': 'requirements.txt'
            }
        }

        mock_get_project_pod.return_value = False

        mock_attempt_pod_launch.return_value = {
            'id': 'new_pod_id',
            'desiredStatus': 'PENDING',
            'runtime': None
        }

        mock_get_pod.return_value = {
            'id': 'new_pod_id',
            'desiredStatus': 'RUNNING',
            'runtime': 'ONLINE'
        }

        mock_ssh_instance = mock_ssh_connection.return_value
        mock_ssh_instance.run_commands.return_value = None

        launch_project()

        mock_attempt_pod_launch.assert_called()
        mock_get_pod.assert_called_with('new_pod_id')
        mock_ssh_connection.assert_called_with('new_pod_id')
        mock_ssh_instance.run_commands.assert_called()
        assert mock_getcwd.called


class TestStartProjectAPI(unittest.TestCase):
    """ Test the start_project_api function. """

    @patch('runpod.cli.groups.project.functions.load_project_config')
    @patch('runpod.cli.groups.project.functions.get_project_pod')
    @patch('runpod.cli.groups.project.functions.SSHConnection')
    @patch('os.getcwd', return_value='/current/path')
    @patch('runpod.cli.groups.project.functions.sync_directory')
    def test_start_project_api_successfully(self, mock_sync_directory, mock_getcwd, mock_ssh_connection, mock_get_project_pod, mock_load_project_config): # pylint: disable=line-too-long
        """ Test that a project API is started successfully. """
        mock_load_project_config.return_value = {
            'project': {
                'uuid': '123456',
                'name': 'test_project',
                'volume_mount_path': '/mount/path',
            },
            'runtime': {
                'handler_path': 'handler.py',
                'requirements_path': 'requirements.txt'
            }
        }

        mock_get_project_pod.return_value = {'id': 'pod_id'}

        mock_ssh_instance = mock_ssh_connection.return_value
        mock_ssh_instance.run_commands.return_value = None

        start_project_api()

        mock_get_project_pod.assert_called_with('123456')
        mock_ssh_connection.assert_called_with({'id': 'pod_id'})
        mock_sync_directory.assert_called_with(mock_ssh_instance, '/current/path', '/mount/path/123456')
        mock_ssh_instance.run_commands.assert_called()
        mock_ssh_instance.close.assert_called()
        assert mock_getcwd.called
