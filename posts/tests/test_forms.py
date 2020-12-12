import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post
from posts.forms import CommentForm


class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        User = get_user_model()
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

        cls.post = Post.objects.create(
            text='Test-text',
            pub_date='26.11.2020',
            author=cls.user,
            group=cls.group
        )

        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_edit_post_in_database(self):
        """При редактировании записи изменяется запись в базе данных
        и не создается новая"""

        form_data = {'text': 'test_post_updated_text'}
        response = FormTests.authorized_client.post(
            reverse('post_edit', kwargs={'username': 'Tihon', 'post_id': '1'}),
            data=form_data,
            follow=True,
            )
        self.assertEqual(Post.objects.count(), 1)
        self.assertRedirects(
            response, reverse(
                'post',
                kwargs={
                    'username': 'Tihon',
                    'post_id': '1'
                    }
                )
            )
        self.post.refresh_from_db()
        self.assertEqual(FormTests.post.text, form_data['text'])

    def test_create_task(self):
        """Валидная форма создает запись c картинкой"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
            )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
            )
        form_data = {
            'group': 1,
            'text': 'Test text',
            'image': uploaded,
            }

        response = FormTests.authorized_client.post(
            reverse('new_post'), data=form_data,
            follow=True
            )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
