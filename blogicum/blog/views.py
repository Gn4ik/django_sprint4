from django.shortcuts import render, redirect, get_object_or_404
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.views.generic import DetailView
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.db.models import Count

User = get_user_model()


def index(request):
    template = "blog/index.html"
    current_time = timezone.now()
    
    posts_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=current_time,
        category__is_published=True
    ).select_related('category', 'location', 'author').annotate(
        comment_count=Count('comments')
        ).order_by('-pub_date')

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, id):
    template = "blog/detail.html"
    current_time = timezone.now()
    post = get_object_or_404(
        Post,
        pk=id,
        is_published=True,
        pub_date__lte=current_time,
        category__is_published=True
    )
    comments = Comment.objects.filter(post=post)
    form = None
    if request.user.is_authenticated:
        form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = "blog/category.html"

    current_time = timezone.now()

    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.objects.filter(
        category=category,
        pub_date__lte=current_time,
        is_published=True).annotate(
        comment_count=Count('comments')
        )
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, template, context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_profile(request):
    instance = request.user
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=instance.username)
    else:
        form = UserForm(instance=instance)
    
    context = {'form': form}
    return render(request, 'blog/user.html', context)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', id=pk)


@login_required
def edit_comment(request, pk, comment_id):
    post = get_object_or_404(Post, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_id)
    form = CommentForm(request.POST)
    if request.user != comment.author:
        return HttpResponseForbidden("Вы не можете " \
        "редактировать этот комментарий")
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=pk)
    else:
        form = CommentForm(instance=comment)
    
    context = {
        'post': post,
        'comment': comment,
        'form': form,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, pk, comment_id):
    post = get_object_or_404(Post, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    
    if request.user != comment.author:
        return HttpResponseForbidden("Вы не можете удалить этот комментарий")
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=pk)
    comments = Comment.objects.filter(post=post).select_related('author')
    
    context = {
        'post': post,
        'comments': comments,
        'delete_comment': comment,
    }
    
    return render(request, 'blog/comment.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post, files=request.FILES or None)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    
    return render(request, 'blog/create.html', context)


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.object
        
        posts = Post.objects.filter(
            author=user,
            is_published=True,
            category__is_published=True
        ).select_related('category', 'location').order_by('-pub_date').annotate(
        comment_count=Count('comments')
        )
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['page_obj'] = page_obj
        context['posts'] = posts
        return context


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ['author']
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            )
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
