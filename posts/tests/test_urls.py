from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls.base import reverse

from posts.models import Group, Post


class UrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        User = get_user_model()
        super().setUpClass()

        cls.user = User.objects.create(
            username='Tihon',
            email='tihon@mail.com',
            password='qwerty123'
        )

        cls.user2 = User.objects.create(
            username='Tihon2',
            email='tihon2@mail.com',
            password='2qwerty123'
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
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        site1 = Site(pk=1, domain='localhost:8000', name='localhost:8000')
        site1.save()

        FlatPage.objects.create(
            url=reverse('about-author'),
            title='О авторе',
            content='немного о себе',
            ).sites.add(site1)

        FlatPage.objects.create(
            url=reverse('about-spec'),
            title='О технологии',
            content='немного о технологии',
            ).sites.add(site1)

    def test_access_guest(self):
        """Страница доступна неавторизованному пользователю."""
        templates_url_names = (
            reverse('index'),
            reverse('group', kwargs={'slug': 'test_slug'}),
            reverse('about-author'),
            reverse('about-spec'),
            reverse('post', kwargs={'username': 'Tihon', 'post_id': '1'}),
            reverse('profile', kwargs={'username': 'Tihon'}),
            reverse('new_post'),
            )
        for url in templates_url_names:
            with self.subTest():
                response = UrlTest.guest.get(url)
                if url == reverse('new_post'):
                    self.assertNotEqual(
                        response.status_code,
                        200, (
                            'Неавторизованный пользователь может'
                            f'попасть на страницу по адресу {url}'
                        )
                    )
                else:
                    self.assertEqual(
                        response.status_code,
                        200, (
                            'Неавторизованный пользователь'
                            f'не может попасть на страницу по адресу {url}'
                            )
                        )

    def test_access_not_author_post(self):
        """Страница редактирования поста доступна
        только авторизованному пользователю-автору"""
        response1 = UrlTest.authorized_client1.get(
            reverse('post_edit', kwargs={'username': 'Tihon', 'post_id': '1'})
            )
        response2 = UrlTest.authorized_client2.get(
            reverse('post_edit', kwargs={'username': 'Tihon', 'post_id': '1'})
            )
        response3 = UrlTest.guest.get(
            reverse('post_edit', kwargs={'username': 'Tihon', 'post_id': '1'})
            )
        self.assertEqual(
            response1.status_code,
            200,
            'У автора поста нет доступа к странице редактирования своего поста'
            )
        self.assertNotEqual(
            response2.status_code,
            200,
            'Пользователь имеет доступ к странице редактирования чужого поста'
            )
        self.assertNotEqual(
            response3.status_code,
            200,
            'Неавторизованный пользователь имеет доступ'
            'к странице редактирования поста'
            )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': 'test_slug'}),
            'new.html': reverse('new_post'),
            'post_new.html': reverse(
                'post_edit',
                kwargs={'username': 'Tihon', 'post_id': '1'}
                ),
            }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = UrlTest.authorized_client1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_redirect(self):
        """Редирект со страницы редактирования
        для тех, у кого нет прав доступа к этой странице."""
        urls = [
            (reverse('post_edit',
                     kwargs={'username': 'Tihon', 'post_id': '1'})),
            (reverse('post',
                     kwargs={'username': 'Tihon', 'post_id': '1'})),
            (reverse('login') + '?next=' + reverse('post_edit',
                                                   kwargs={
                                                       'username': 'Tihon',
                                                       'post_id': '1'
                                                       }))
        ]
        response1 = UrlTest.authorized_client2.get(urls[0])
        response2 = UrlTest.guest.get(urls[0])
        self.assertRedirects(response1, urls[1])
        self.assertRedirects(response2, urls[2])

    def test_404(self):
        response = UrlTest.guest.get('/404/')
        self.assertEqual(
            response.status_code,
            404,
            'Сервер не возвращает код 404, если страница не найдена'
            )
