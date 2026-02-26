import pytest

if __name__ == '__main__':
    pytest.main(['-v', 'services/attendance-service/tests', '--tb=short'], plugins=[])
