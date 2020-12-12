from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        User = get_user_model()
        super().setUpClass()

        cls.user = User.objects.create(
            username='Tihon',
            email='tihon@mail.com',
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

        cls.post = Post.objects.create(
            text='Test-text',
            pub_date='26.11.2020',
            author=cls.user,
            group=cls.group1
        )

        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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

    def test_pages_uses_correct_template(self):
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
        text_test = response.context.get('page')[0].text
        self.assertEqual(text_test, 'Test-text')
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
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(post, 'Test-text')

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
        self.assertEqual(text, 'Test-text')
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
        self.assertEqual(text, 'Test-text')
        self.assertEqual(post_count, 1)
        self.assertEqual(name, 'Tihon')

    def test_new_show_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = ViewsTest.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
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
