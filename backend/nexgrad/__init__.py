# Nexgrad Django Project Package
try:
    import pymysql
    pymysql.install_as_MySQLdb()

    # Bypass strict version check and features for XAMPP MariaDB 10.4 compatibility
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.mysql.features import DatabaseFeatures

    BaseDatabaseWrapper.check_database_version_supported = lambda self: None
    DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
except ImportError:
    pass



