from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AppTokenGenerator(PasswordResetTokenGenerator):
    """Token generator used for account activation links."""

    def _make_hash_value(self, user, timestamp):
        # No longer uses `six.text_type` — just str() in Python 3
        return str(user.is_active) + str(user.pk) + str(timestamp)


account_activation_token = AppTokenGenerator()
