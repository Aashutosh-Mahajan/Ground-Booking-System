from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_studentuser_branch_studentuser_division_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='sport',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
