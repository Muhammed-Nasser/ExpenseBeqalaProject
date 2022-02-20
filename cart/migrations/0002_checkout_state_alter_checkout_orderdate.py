# Generated by Django 4.0.2 on 2022-02-20 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkout',
            name='state',
            field=models.CharField(choices=[('open', 'OPEN'), ('pending', 'PENDING'), ('done', 'DONE')], default='open', max_length=8),
        ),
        migrations.AlterField(
            model_name='checkout',
            name='orderDate',
            field=models.DateTimeField(null=True),
        ),
    ]
