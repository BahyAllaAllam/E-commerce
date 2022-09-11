from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import image_upload


class ProfileModelTest(TestCase):
    print("Class: Testing_users_app_models_profile.")

    @classmethod
    def setUpTestData(cls):
        print("Setting_up_data_for_testing_users_models")
        cls.user = User.objects.create(username='big', email='big@compony.com')

    def test_profile_image_height_width(self):
        print("Method: testing_profile_model_image_height_width_must_be_less_than_or_"
              "equal_to_300.")
        self.assertTrue(self.user.profile.image.width <= 300)
        self.assertTrue(self.user.profile.image.height <= 300)

    def test_profile_image_name(self):
        print("Method: testing_profile_model_image_name.")
        self.assertEqual(self.user.profile.image.name, 'profile/default.jpg')
        self.user.profile.image = SimpleUploadedFile(name=image_upload(self.user.profile, 'job_api_file.PNG'),
                                                     content=open('C:\PRIVATE\WORK\job_api_file.PNG', 'rb').read(),
                                                     content_type='image/jpeg/png')
        self.assertEqual(self.user.profile.image.name, 'big.PNG')

    def test_profile_image_exist(self):
        print("Method: testing_profile_model_if_image_exist.")
        self.assertTrue(self.user.profile.image)

    def test_user_email_is_unique(self):
        print("Method: test_user_email_is_unique.")
        self.assertTrue(self.user._meta.get_field('email')._unique)

    def test_object_name_as_expected(self):
        print("Method: test_object_name_as_expected.")
        expected_object_name = f"{self.user.username} Profile"
        self.assertEqual(str(self.user.profile), expected_object_name)

    def test_if_user_profile_exist(self):
        print("Method: test_if_user_profile_exist.")
        self.assertTrue(self.user.profile)
