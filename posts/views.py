from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'index.html',
        {'page': page, 'paginator': paginator}
        )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 2)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'group.html', {
            'page': page,
            'paginator': paginator,
            'group': group,
            }
        )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.author_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = Follow.objects.filter(
        author=author,
        user=request.user.id
        ).exists()
    follower = Follow.objects.filter(author=author).count()
    follows = Follow.objects.filter(user=author).count()
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'paginator': paginator,
        'posts_count': author.author_posts.count(),
        'following': following,
        'follower': follower,
        'follows': follows,
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    following = Follow.objects.filter(
        author=post.author,
        user=request.user.id
        )
    follower = Follow.objects.filter(author=post.author).count()
    follows = Follow.objects.filter(user=post.author).count()
    return render(request, 'post.html', {
        'author': post.author,
        'post': post,
        'posts_count': post.author.author_posts.count(),
        'comments': comments,
        'form': form,
        'following': following,
        'follower': follower,
        'follows': follows,
        })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user.username == username:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
            )
        if not form.is_valid():
            return render(
                request,
                'post_new.html',
                {'form': form, 'post': post}
                )
        form.save()
        return redirect('post', post.author.username, post_id)
    return redirect('post', post.author.username, post_id)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {'page': page, 'paginator': paginator}
        )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if not follow and author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow:
        follow.delete()
    return redirect('profile', username)
