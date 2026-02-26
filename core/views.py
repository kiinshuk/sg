from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Profile, Post, Like, Follow, Comment
from .forms import SignUpForm, LoginForm, ProfileUpdateForm, PostForm, CommentForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        
        # ✅ This won't cause IntegrityError
        Profile.objects.get_or_create(user=user)
        
        login(request, user)
        messages.success(request, f'Welcome to Snapgram, {user.username}!')
        return redirect('feed')
    
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'feed')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def feed(request):
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    posts = Post.objects.filter(
        Q(user__in=following_users) | Q(user=request.user)
    ).select_related('user', 'user__profile').prefetch_related('likes', 'comments')
    
    # Suggested users (not following, not self)
    suggested = User.objects.exclude(
        id__in=following_users
    ).exclude(id=request.user.id).select_related('profile')[:5]

    comment_form = CommentForm()
    # Annotate liked post ids for template
    liked_post_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    return render(request, 'core/feed.html', {
        'posts': posts,
        'suggested': suggested,
        'comment_form': comment_form,
        'liked_post_ids': liked_post_ids,
    })


@login_required
def explore(request):
    posts = Post.objects.all().select_related('user', 'user__profile').prefetch_related('likes')
    return render(request, 'core/explore.html', {'posts': posts})


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=profile_user)
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    followers = Follow.objects.filter(following=profile_user).select_related('follower')
    following = Follow.objects.filter(follower=profile_user).select_related('following')

    return render(request, 'core/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
        'followers': followers,
        'following': following,
    })


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        # Update name fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile', username=request.user.username)
    return render(request, 'core/edit_profile.html', {'form': form})


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        if not post.image and not post.video:
            messages.error(request, 'Please upload an image or video.')
            return render(request, 'core/create_post.html', {'form': form})
        post.save()
        messages.success(request, 'Post shared!')
        return redirect('feed')
    return render(request, 'core/create_post.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted.')
    return redirect('profile', username=request.user.username)


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('user', 'user__profile')
    comment_form = CommentForm()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post_detail', post_id=post_id)
    liked = Like.objects.filter(user=request.user, post=post).exists()
    return render(request, 'core/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'liked': liked,
    })


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes_count()})


@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        following = False
    else:
        following = True
    followers_count = Follow.objects.filter(following=target).count()
    return JsonResponse({'following': following, 'followers_count': followers_count})


@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')[:20]
    return render(request, 'core/search.html', {'results': results, 'query': query})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
    return redirect(request.META.get('HTTP_REFERER', 'feed'))
