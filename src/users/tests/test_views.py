# from django.http import HttpRequest
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core import mail
from users.utils import account_activation_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class RegisterViewTest(TestCase):
    print("Class: Testing_users_app_views_register.")

    @classmethod
    def setUpTestData(cls):
        print("ClassMethod: Setting_up_data_for_testing_register_view")
        cls.user = User.objects.create(username='big', email='big@company.com', password='foo')
        cls.valid_user = {'username': 'john', 'email': 'john@company.com', 'password1': '1234admin',
                          'password2': '1234admin'}
        cls.invalid_user = {'username': 'john', 'email': 'john@company.com', 'password1': '1234admin',
                            'password2': '123admin'}

    def test_rendering_register_page_with_anonymous_user(self):
        print("Method: testing_view_register_page_and_template_used_with_anonymous_user")
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_rendering_register_page_with_authenticated_user(self):
        print("Method: testing_view_register_page_and_template_used_with_authenticated_user")
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:register'))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertIn('You have to logout first!', messages)

    def test_register_valid_user(self):
        print("Method: testing_register_new_valid_user")
        response = self.client.post(reverse('users:register'), self.valid_user)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        user = User.objects.get(username='john')
        mails = [m.subject for m in mail.outbox]
        # Testing_if_registration_process_is_successful
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertTemplateUsed(response, 'mail_body.txt', 'mail_body.html')
        self.assertIn('We have sent you an email to verify your account, please check your mail!', messages)
        # Testing_if_user_is_inactive
        self.assertFalse(user.is_active)
        # Testing_activation_mail_were_sent_after_registration
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Email Verification', mails)

    def test_register_invalid_user(self):
        print("Method: testing_register_invalid_user")
        response = self.client.post(reverse('users:register'), self.invalid_user)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')


class ActivateUserViewTest(TestCase):
    print("Class: Testing_users_app_views_activate_user.")

    def setUp(self):
        print("ClassMethod: Setting_up_data_for_testing_activate_view")
        self.valid_user = {'username': 'john', 'email': 'john@company.com', 'password1': '1234admin',
                           'password2': '1234admin'}
        self.response = self.client.post(reverse('users:register'), self.valid_user)
        self.mails = [m.subject for m in mail.outbox]

    def test_if_user_is_inactive_before_activation(self):
        print("Method: test_if_user_is_inactive_before_activation")
        self.assertFalse(User.objects.get(username='john').is_active)

    def test_if_user_is_activated_with_valid_token(self):
        print("Method: test_if_user_is_activated_with_valid_token")
        user = User.objects.get(username='john')
        parameters = [urlsafe_base64_encode(force_bytes(user.pk)), account_activation_token.make_token(user)]
        response = self.client.post(reverse('users:activate', args=parameters))
        self.assertEqual(response.url, reverse('login'))
        self.assertTrue(User.objects.get(username='john').is_active)

    def test_if_user_is_activated_with_invalid_credentials(self):
        print("Method: test_if_user_is_activated_with_invalid_credentials")
        user = User.objects.create()
        john = User.objects.get(username='john')
        invalid_token = self.client.post(reverse('users:activate', args=[urlsafe_base64_encode(force_bytes(john.pk)), account_activation_token.make_token(user)]))
        self.assertEqual(invalid_token.url, reverse('users:register'))
        self.assertFalse(User.objects.get(username='john').is_active)
        invalid_user = self.client.post(reverse('users:activate', args=[urlsafe_base64_encode(force_bytes(john.pk+3)), account_activation_token.make_token(john)]))
        self.assertEqual(invalid_user.url, reverse('users:register'))


class ChangeEmailTest(TestCase):
    print("Class: Testing_users_app_views_change_email.")

    @classmethod
    def setUpTestData(cls):
        print("ClassMethod: Setting_up_data_for_testing_change_email_view")
        cls.user = User.objects.create(username='big', email='big@company.com')

    def setUp(self):
        self.client.force_login(self.user)

    def test_change_email_rendering_right_page(self):
        print("Method: test_change_email_rendering_right_page")
        response = self.client.get(reverse('users:change_email', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/change_email.html')

    def test_change_email_with_valid_email(self):
        print("Method: test_change_email_with_valid_email")
        response = self.client.post(reverse('users:change_email', args=[self.user.username]),
                                    {'email': 'b@company.com'})
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertIn('We have sent you an email to verify your account, please check your mail!', messages)

    def test_change_email_with_invalid_email(self):
        print("Method: test_change_email_with_invalid_email")
        response = self.client.post(reverse('users:change_email', args=[self.user.username]), {'email': 'b@company'})
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:change_email', args=[self.user.username]))
        self.assertIn('Please write a valid email.', messages)

    def test_change_email_with_same_old_email(self):
        print("Method: test_change_email_with_same_old_email")
        response = self.client.post(reverse('users:change_email', args=[self.user.username]),
                                    {'email': self.user.email})
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:change_email', args=[self.user.username]))
        self.assertIn('Please Enter A Different Email Address !', messages)


class ProfileViewTest(TestCase):
    print("Class: Testing_users_app_views_profile.")

    @classmethod
    def setUpTestData(cls):
        print("ClassMethod: Setting_up_data_for_testing_profile_view")
        cls.user = User.objects.create(username='big', email='big@company.com')

    def setUp(self):
        self.client.force_login(self.user)

    def test_profile_rendering_right_page(self):
        print("Method: test_change_email_rendering_right_page")
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_edit_with_valid_data(self):
        print("Method: test_profile_edit_with_valid_data")
        response = self.client.post(reverse('users:profile'),
                                    {'first_name': 'Bahy', 'last_name': 'Allam', 'image': 'profile/test.jpg'})
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:profile'))
        self.assertIn('Your account has been updated!', messages)


class DeleteUserViewTest(TestCase):
    print("Class: Testing_users_app_views_delete_user.")

    @classmethod
    def setUpTestData(cls):
        print("ClassMethod: Setting_up_data_for_testing_delete_user_view")
        cls.user = User.objects.create(username='big', email='big@company.com')
        cls.john = User.objects.create(username='john', email='john@company.com')

    def setUp(self):
        self.client.force_login(self.user)

    def test_delete_user_rendering_right_page(self):
        print("Method: test_delete_user_rendering_right_page")
        response = self.client.get(reverse('users:delete-user', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/delete_user.html')

    def test_deleting_user(self):
        print("Method: testing_deleting_user")
        response = self.client.post(reverse('users:delete-user', args=[self.user.username]))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertIn('Your account has been deleted successfully !', messages)

    def test_delete_user_another_user(self):
        print("Method: test_delete_user_another_user")
        response = self.client.post(reverse('users:delete-user', args=[self.john.username]))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:profile'))
        self.assertIn('Oops you do not have permission to do that!', messages)
