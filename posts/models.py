from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import UniqueConstraint

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст', help_text='Пиши что хочешь')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='author_posts'
        )
    group = models.ForeignKey(
        'Group', models.SET_NULL, blank=True, null=True,
        related_name='group_posts',
        verbose_name='Группа', help_text='Выбери группу'
        )
    image = models.ImageField(
        upload_to='posts/',
        verbose_name='Картинка',
        help_text='Загружай',
        blank=True, null=True
        )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(null=False, unique=True, max_length=20)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        'Post', on_delete=models.CASCADE, related_name='comments',
        verbose_name='Откоментированный пост'
        )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Автор коммента'
        )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Добавь коментарий'
        )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower'
        )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following'
        )

    class Meta:
        UniqueConstraint(fields=['user', 'author'], name='follow',)
        db_table = 'follow'
