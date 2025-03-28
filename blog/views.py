from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Post, Category
from .forms import CommentForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string 

# Create your views here.
def home(request):
    posts = Post.objects.filter(is_published=True).order_by('-created_at')
    print("Fetched Posts:", posts)  # Debug print
    categories = Category.objects.all()
    paginator = Paginator(posts, 5)  # Shows 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/home.html', {'page_obj': page_obj, 'category_list': categories, 'posts': posts})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    comments = post.comments.filter(approved=True).order_by('-created_at')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            if request.user.is_authenticated:
                new_comment.user = request.user
            new_comment.approved = True
            new_comment.save()
            
            comment_html = render_to_string('blog/comment_partial.html', {'comment': new_comment})
            return JsonResponse({'comment_html': comment_html}, status=200)
        else:
            return JsonResponse({'error': 'Invalid comment form'}, status=400)
        
    comment_form = CommentForm()
    return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form})


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, is_published=True).order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'blog/category_posts.html', {'category': category, 'posts': posts, 'category_list': categories})

def search_posts(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(title__icontains=query, is_published=True) if query else []
    categories = Category.objects.all()  # Fetch categories to display on search page
    return render(request, 'blog/search_results.html', {'query': query, 'posts': posts, 'category_list': categories})

@login_required
def dashboard(request):
    return render(request, 'blog/dashboard.html')

def user_login(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('blog:dashboard')
        else:
            error_message = "Invalid credentials. Please try again."

    return render(request, 'blog/login.html', {'error': error_message})

@login_required
def like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"liked": liked, "total_likes": post.total_likes()})

def user_logout(request):
    logout(request)
    return redirect('blog:home')
