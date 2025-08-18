import unittest
from unittest.mock import patch, MagicMock
import pytest

# Try importing tkinter and gui_dashboard, skip tests if not available
try:
    import tkinter as tk
    from gui_dashboard import GUIDashboard
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    tk = None
    GUIDashboard = None

@pytest.mark.skipif(not GUI_AVAILABLE, reason="tkinter or gui_dashboard not available")
class TestGUIDashboard(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = GUIDashboard(self.root)

    def tearDown(self):
        self.root.destroy()

    @patch('gui_dashboard.psutil.cpu_percent')
    @patch('gui_dashboard.psutil.virtual_memory')
    @patch('gui_dashboard.psutil.disk_usage')
    def test_update_system_health(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        mock_cpu_percent.return_value = 50
        mock_virtual_memory.return_value.percent = 60
        mock_disk_usage.return_value.percent = 70

        self.app.update_system_health()

        self.assertEqual(self.app.cpu_label.cget("text"), "CPU Usage: 50%")
        self.assertEqual(self.app.memory_label.cget("text"), "Memory Usage: 60%")
        self.assertEqual(self.app.disk_label.cget("text"), "Disk Usage: 70%")

    @patch('gui_dashboard.Path')
    @patch('gui_dashboard.json.load')
    def test_update_activity_logs(self, mock_json_load, mock_path):
        mock_path.return_value.iterdir.return_value = [MagicMock(is_dir=lambda: True, __truediv__=lambda x: x)]
        mock_json_load.return_value = [{"time": "2023-01-01 00:00:00", "description": "Test log"}]

        self.app.update_activity_logs()

        self.assertIn("2023-01-01 00:00:00: Test log\n", self.app.logs_text.get("1.0", tk.END))

    @patch('gui_dashboard.ActivityRegulator.add_task')
    def test_add_task(self, mock_add_task):
        self.app.add_task_entry.insert(0, "Test Task")
        self.app.add_task()

        mock_add_task.assert_called_once_with("Test Task", unittest.mock.ANY)
        self.assertIn("Test Task", self.app.task_listbox.get(0, tk.END))

    @patch('gui_dashboard.ActivityRegulator.remove_task')
    def test_remove_task(self, mock_remove_task):
        self.app.task_listbox.insert(tk.END, "Test Task")
        self.app.task_listbox.select_set(0)
        self.app.remove_task()

        mock_remove_task.assert_called_once_with("Test Task")
        self.assertNotIn("Test Task", self.app.task_listbox.get(0, tk.END))

if __name__ == "__main__":
    if GUI_AVAILABLE:
        unittest.main()
    else:
        print("Skipping GUI tests - tkinter or gui_dashboard not available")
