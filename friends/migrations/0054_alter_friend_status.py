# Generated by Django 3.2.10 on 2022-06-23 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0053_auto_20220517_0527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friend',
            name='status',
            field=models.CharField(choices=[('3', 'Not a Friends'), ('1', 'Friends'), ('2', 'Remove friend'), ('0', 'Pending')], default='0', max_length=5, verbose_name='Status'),
        ),
    ]
