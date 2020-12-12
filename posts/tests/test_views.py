import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post


class ViewsTest(TestCase):
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

        cls.user2 = User.objects.create(
            username='Tihon2',
            email='tihon2@mail.com',
            password='qwerty123'
        )

        cls.group1 = Group.objects.create(
            title='test-group1',
            description='test-description1',
            slug='test_slug1'
        )

        cls.group2 = Group.objects.create(
            title='test-group2',
            description='test-description2',
            slug='test_slug2'
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
            )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
            )

        cls.form_data = {
            'group': 1,
            'text': 'Test-2',
            'image': cls.uploaded,
            }

        cls.post = Post.objects.create(
            text='Test-1',
            pub_date='26.11.2020',
            author=cls.user,
            group=cls.group1
        )

        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client2 = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2.force_login(cls.user2)

        site1 = Site(pk=1, domain='localhost:8000', name='localhost:8000')
        site1.save()

        cls.flatpage1 = FlatPage.objects.create(
            url=reverse('about-author'),
            title='О авторе',
            content='немного о себе',
            ).sites.add(site1)

        cls.flatpage2 = FlatPage.objects.create(
            url=reverse('about-spec'),
            title='О технологии',
            content='немного о технологии',
            ).sites.add(site1)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_about_page_show_correct_context(self):
        """Шаблон about-spec about-autor сформирован
         с правильным контекстом."""
        response1 = ViewsTest.guest.get(reverse('about-spec'))
        response2 = ViewsTest.guest.get(reverse('about-author'))
        context1 = response1.context.get('flatpage')
        context2 = response2.context.get('flatpage')
        self.assertEqual(context1.content, 'немного о технологии')
        self.assertEqual(context1.title, 'О технологии')
        self.assertEqual(context1.url, reverse('about-spec'))
        self.assertEqual(context2.content, 'немного о себе')
        self.assertEqual(context2.title, 'О авторе')
        self.assertEqual(context2.url, reverse('about-author'))

    def test_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': 'test_slug1'}),
            'new.html': reverse('new_post'),
            }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = ViewsTest.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон для index сформирован с правильным контекстом."""
        response = ViewsTest.guest.get(reverse('index'))
        test = response.context.get('page')[0]
        self.assertEqual(test.text, 'Test-1')
        self.assertEqual(test.author, ViewsTest.user)
        self.assertEqual(test.group, ViewsTest.group1)
        self.assertLessEqual(len(
            response.context.get('page').object_list),
            10,
            'Записей на одной странице больше 10'
            )

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = ViewsTest.guest.get(
            reverse('group', kwargs={'slug': 'test_slug1'})
            )
        group_title = response.context.get('group').title
        group_description = response.context.get('group').description
        group_slug = response.context.get('group').slug
        self.assertEqual(group_title, 'test-group1')
        self.assertEqual(group_slug, 'test_slug1')
        self.assertEqual(group_description, 'test-description1')

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = ViewsTest.authorized_client.get(
            reverse('post_edit', kwargs={'username': 'Tihon', 'post_id': '1'})
            )
        post = ViewsTest.post.text
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(post, 'Test-1')

    def test_profile_show_correct_context(self):
        """Шаблон для профиля пользователя
        сформирован с правильным контекстом."""
        response = ViewsTest.authorized_client.get(
            reverse('profile', kwargs={'username': 'Tihon'})
            )
        name = response.context.get('author').username
        text = response.context.get('page')[0].text
        posts_count = response.context.get('posts_count')
        self.assertEqual(name, 'Tihon')
        self.assertEqual(text, 'Test-1')
        self.assertEqual(posts_count, 1)
        self.assertLessEqual(
            len(response.context.get('page').object_list),
            2,
            'Записей на одной странице больше 10'
            )

    def test_post_page_show_correct_context(self):
        """Шаблон для post сформирован с правильным контекстом."""
        response = ViewsTest.guest.get(
            reverse('post', kwargs={'username': 'Tihon', 'post_id': '1'})
            )
        post_count = response.context.get('posts_count')
        name = response.context.get('author').username
        text = response.context.get('post').text
        self.assertEqual(text, 'Test-1')
        self.assertEqual(post_count, 1)
        self.assertEqual(name, 'Tihon')

    def test_new_show_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = ViewsTest.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_list_page_list_is_1(self):
        """Запись с постом появлятся на
        главной странице и на странице группы"""
        response1 = ViewsTest.authorized_client.get(reverse('index'))
        response2 = ViewsTest.authorized_client.get(
            reverse('group', kwargs={'slug': 'test_slug1'})
            )
        response3 = ViewsTest.authorized_client.get(
            reverse('group', kwargs={'slug': 'test_slug2'})
            )
        self.assertEqual(
            len(response1.context['page']),
            1,
            'Запись не появилсь на главной'
            )
        self.assertEqual(
            len(response2.context['page']),
            1,
            'Запись не появилсь на странице группы'
            )
        self.assertEqual(
            len(response3.context['page']),
            0,
            'Запись не появилсь на странице группы'
            )

    def test_comments(self):
        """Авторизованный пользователь может оставлять комментарии"""
        comment_count = Comment.objects.count()
        form_data3 = {
            'author': ViewsTest.user,
            'post': ViewsTest.post,
            'text': 'Comment 1',
        }
        ViewsTest.authorized_client2.post(reverse('add_comment', kwargs={
            'username': ViewsTest.user.username,
            'post_id': ViewsTest.post.id
            }),
            data=form_data3,
            follow=True,
            )
        post_comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(post_comment.text, 'Comment 1')
        self.assertEqual(post_comment.author, self.user2)
        self.assertEqual(post_comment.post, self.post)
        self.assertFalse(Comment.objects.filter(text='Comment 2'))

    def test_guest_make_comments(self):
        """Неавторизованный пользователь не может оставлять комментарии"""
        comment_count = Comment.objects.count()
        form_data2 = {
            'author': ViewsTest.user,
            'post': ViewsTest.post,
            'text': 'Comment 2',
        }
        ViewsTest.guest.post(reverse('add_comment', kwargs={
            'username': ViewsTest.user.username,
            'post_id': ViewsTest.post.id
            }),
            data=form_data2,
            follow=True
            )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(Comment.objects.filter(text='Comment 2'))

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        follow_count1 = Follow.objects.filter(
            user=ViewsTest.user2,
            author=ViewsTest.user
            ).count()
        Follow.objects.create(user=ViewsTest.user, author=ViewsTest.user2)
        ViewsTest.authorized_client2.post(reverse('profile_follow', kwargs={
            'username': ViewsTest.user.username
            }))
        ViewsTest.authorized_client.post(reverse('profile_unfollow', kwargs={
            'username': ViewsTest.user2.username
            }))
        self.assertEqual(Follow.objects.count(), follow_count1 + 1)
        self.assertFalse(Follow.objects.filter(
            user=ViewsTest.user,
            author=ViewsTest.user2
            ))

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться"""
        Follow.objects.create(user=ViewsTest.user, author=ViewsTest.user2)
        follow_count1 = Follow.objects.filter(
            user=ViewsTest.user,
            author=ViewsTest.user2
            ).count()
        ViewsTest.authorized_client.post(reverse('profile_unfollow', kwargs={
            'username': ViewsTest.user2.username
            }))
        self.assertEqual(Follow.objects.count(), follow_count1 - 1)
        self.assertFalse(Follow.objects.filter(
            user=ViewsTest.user,
            author=ViewsTest.user2
            ))

    def test_follow_index(self):
        """Запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан"""
        ViewsTest.authorized_client2.post(reverse('profile_follow', kwargs={
            'username': ViewsTest.user.username
            }))
        response1 = ViewsTest.authorized_client.get(reverse('follow_index'))
        response2 = ViewsTest.authorized_client2.get(reverse('follow_index'))
        post_follow_index1 = response1.context.get('page')
        post_follow_index2 = response2.context.get('page')[0]
        self.assertFalse(post_follow_index1)
        self.assertEqual(post_follow_index2, ViewsTest.post)

    def test_image_upload(self):
        """Картинка загружается на страницы"""
        ViewsTest.authorized_client.post(
            reverse('new_post'), data=ViewsTest.form_data,
            follow=True
            )
        response1 = ViewsTest.guest.get(reverse('index'))
        response2 = ViewsTest.guest.get(reverse('profile', kwargs={
            'username': ViewsTest.user.username
            }))
        response3 = ViewsTest.guest.get(reverse('post', kwargs={
            'username': ViewsTest.user.username, 'post_id': '2'
            }))
        response4 = ViewsTest.guest.get(reverse('group', kwargs={
            'slug': 'test_slug1'
            }))
        image1 = response1.context.get('page')[0].image
        image2 = response2.context.get('page')[0].image
        image3 = response3.context.get('post').image
        image4 = response4.context.get('page')[0].image
        self.assertEqual(image1.name, 'posts/small.gif')
        self.assertEqual(image2.name, 'posts/small.gif')
        self.assertEqual(image3.name, 'posts/small.gif')
        self.assertEqual(image4.name, 'posts/small.gif')

    def test_not_image_upload(self):
        """Загрузка не картинки"""
        file = b'\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82'
        uploaded1 = SimpleUploadedFile(
            name='test.txt',
            content=file,
            content_type='txt/txt'
            )
        form_data1 = {
            'group': ViewsTest.group1.id,
            'text': 'third unique post',
            'image': uploaded1,
        }
        response = ViewsTest.authorized_client.post(
            reverse('new_post'),
            data=form_data1,
            follow=True,
        )
        expected_error = ['Загрузите правильное изображение.'
                          'Файл, который вы загрузили, '
                          'поврежден или не является изображением.']
        self.assertFormError(response, 'form', 'image', expected_error)
