from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("settlement", "0002_payment_paymentreversal_payment_payment_session_and_more"),
        ("ledger", "0005_amounts_instead_of_chips"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="transfer", name="transfer_amount_positive"),
        migrations.RemoveConstraint(model_name="payment", name="payment_amount_positive"),
        migrations.RenameField("transfer", "amount_centavos", "amount"),
        migrations.RenameField("payment", "amount_centavos", "amount"),
    ]
