from django.test import TestCase
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, EmailChangeForm


class UserRegisterFormTest(TestCase):
    print("Class: Testing_users_app_forms_register_form.")
    form = UserRegisterForm()

    def test_email_help_text(self):
        print("Method: testing_register_form_email_help_text [Required.].")
        self.assertEqual(self.form.fields['email'].help_text, "Required.")

    def test_fields_label(self):
        print("Method: testing_register_form_fields_label "
              "[Username, Email, Password, Password confirmation].")

        for field in self.form.fields:
            self.assertIn(self.form.fields[field].label,
                          ['Username', 'Email', 'Password', 'Password confirmation'])

    def test_fields_should_exist(self):
        print("Method: testing_register_form_fields_should_exist "
              "[username, email, password, password confirmation].")

        for field in self.form.fields:
            self.assertIn(field, ['username', 'email', 'password1', 'password2'])


class UserUpdateFormTest(TestCase):
    print("Class: Testing_users_app_forms_user_update_form.")
    form = UserUpdateForm()

    def test_fields_label(self):
        print("Method: testing_user_update_form_fields_label "
              "[First name, Last name].")

        for field in self.form.fields:
            self.assertIn(self.form.fields[field].label, ['First name', 'Last name'])

    def test_fields_should_exist(self):
        print("Method: testing_user_update_form_fields_should_exist "
              "[first_name, last_name].")

        for field in self.form.fields:
            self.assertIn(field, ['first_name', 'last_name'])


class ProfileUpdateFormTest(TestCase):
    print("Class: Testing_users_app_forms_profile_update_form.")
    form = ProfileUpdateForm()

    def test_fields_label(self):
        print("Method: testing_profile_update_form_fields_label [Image].")
        self.assertEqual(self.form.fields['image'].label, 'Image')

    def test_fields_should_exist(self):
        print("Method: testing_profile_update_form_field_should_exist [image].")
        self.assertTrue(self.form.fields['image'])


class EmailChangeFormTest(TestCase):
    print("Class: Testing_users_app_forms_email_change_form.")
    form = EmailChangeForm()

    def test_fields_should_exist(self):
        print("Method: testing_email_change_form_fields_should_exist [email].")
        self.assertTrue(self.form.fields['email'])

    def test_fields_label(self):
        print("Method: testing_email_change_form_fields_label [email].")
        self.assertEqual(self.form.fields['email'].label, 'Email')

    def test_email_help_text(self):
        print("Method: testing_email_change_form_email_help_text [Required.].")
        self.assertEqual(self.form.fields['email'].help_text, "Required.")
