import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from posts.models import Group, Post


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create(
            username='Tihon',
            email='tihon@mail.com',
            password='qwerty123'
            )
        cls.group = Group.objects.create(
            title='test-group',
            description='test-description',
            slug='test_slug'
            )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
            )
        uploaded1 = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
            )

        cls.post = Post.objects.create(
            text='Test-text',
            pub_date='26.11.2020',
            author=cls.user,
            group=cls.group,
            image=uploaded1
        )
        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = ModelTest.post
        field_verboses = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка'
            }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = ModelTest.post
        field_help_texts = {
            'text': 'Пиши что хочешь',
            'group': 'Выбери группу',
            }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_str_group(self):
        """отображение значения поля __str__ в объектах моделей Group"""
        group = ModelTest.group
        self.assertEqual(group.__str__(), str(group))

    def test_str_post(self):
        """отображение значения поля __str__ в объектах моделей Post"""
        post = ModelTest.post
        self.assertLessEqual(len(post.__str__()), 15)
