# Generated by Django 2.2.12 on 2021-03-22 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0009_arm2800_odotusvaiheen_pituus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arm2300',
            name='konevaiheen_pituus',
        ),
    ]
