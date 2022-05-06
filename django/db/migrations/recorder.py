from django.apps.registry import Apps
from django.db import DatabaseError, models
from django.utils.functional import classproperty
from django.utils.timezone import now

from .exceptions import MigrationSchemaMissing

# 关联的表：django_migrations
class MigrationRecorder:
    """
    Deal with storing migration records in the database.

    Because this table is actually itself used for dealing with model
    creation, it's the one thing we can't do normally via migrations.
    We manually handle table creation/schema updating (using schema backend)
    and then have a floating model to do queries with.

    If a migration is unapplied its row is removed from the table. Having
    a row in the table always means a migration is applied.
    """
    _migration_class = None

    @classproperty
    def Migration(cls):
        """
        Lazy load to avoid AppRegistryNotReady if installed apps import
        MigrationRecorder.
        """
        if cls._migration_class is None:
            class Migration(models.Model):  # 定义迁移的模型类
                app = models.CharField(max_length=255)  # 应用名称
                name = models.CharField(max_length=255)  # 迁移文件名称
                applied = models.DateTimeField(default=now)  # 操作时间

                class Meta:
                    apps = Apps()  # App对象
                    app_label = 'migrations'  # 应用标签
                    db_table = 'django_migrations'  # 表名

                def __str__(self):
                    return 'Migration %s for %s' % (self.name, self.app)

            cls._migration_class = Migration
        return cls._migration_class  # 返回迁移类

    def __init__(self, connection):  # 第二章 讲 ORM 框架时说
        self.connection = connection

    @property
    def migration_qs(self):
        # 使用的数据库
        # self.connection.alias 默认的是项目 settings.py 中数据库配置中的 default
        return self.Migration.objects.using(self.connection.alias)

    def has_table(self):
        """Return True if the django_migrations table exists."""
        with self.connection.cursor() as cursor:
            # 返回数据库中的所有表
            tables = self.connection.introspection.table_names(cursor)
        return self.Migration._meta.db_table in tables

    def ensure_schema(self):
        """Ensure the table exists and has the correct schema."""
        # If the table's there, that's fine - we've never changed its schema
        # in the codebase.
        if self.has_table():
            return
        # Make the table
        try:
            with self.connection.schema_editor() as editor:
                editor.create_model(self.Migration)
        except DatabaseError as exc:
            raise MigrationSchemaMissing("Unable to create the django_migrations table (%s)" % exc)

    def applied_migrations(self):
        """
        Return a dict mapping (app_name, migration_name) to Migration instances
        for all applied migrations.
        """
        if self.has_table():
            # 用一个元祖表示key，用迁移记录表示的value
            return {(migration.app, migration.name): migration for migration in self.migration_qs}
        else:
            # If the django_migrations table doesn't exist, then no migrations
            # are applied.
            return {}

    def record_applied(self, app, name):
        """Record that a migration was applied."""
        self.ensure_schema()
        self.migration_qs.create(app=app, name=name)  # 生成一条迁移记录到django_migrations


    def record_unapplied(self, app, name):
        """Record that a migration was unapplied."""
        self.ensure_schema()
        self.migration_qs.filter(app=app, name=name).delete()  # 删除django_migrations中的一条迁移记录

    def flush(self):
        """Delete all migration records. Useful for testing migrations."""
        # 删除django_migrations中的所有迁移记录
        self.migration_qs.all().delete()
