#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks. set environment variables file is the backend.settings.py"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        # 引入 Django 的命令行工具函数，它可以处理各种管理命令。
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHON environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # 执行你在命令行输入的命令，比如 runserver、make migrations 等。
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
