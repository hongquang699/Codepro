from django.db import migrations


def add_pypy_language(apps, schema_editor):
    Language = apps.get_model('judge', 'Language')
    Language.objects.using(schema_editor.connection.alias).get_or_create(
        key='PYPY3',
        defaults={
            'name': 'PyPy 3',
            'short_name': 'PyPy 3',
            'common_name': 'Python',
            'ace_mode_name': 'python',
            'pygments_style': 'python',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [('judge', '0009_code_share')]

    operations = [migrations.RunPython(add_pypy_language, migrations.RunPython.noop)]
