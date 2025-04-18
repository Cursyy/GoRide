from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Review
import json

@login_required
def submit_review(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text')
            rating = data.get('rating')

            if not text or not rating:
                return JsonResponse({'success': False, 'error': 'Text and rating are required'}, status=400)

            review = Review.objects.create(
                user=request.user,
                text=text,
                rating=rating,
            )
            return JsonResponse({'success': True, 'message': 'Review submitted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


from django.shortcuts import render
from django.core.paginator import Paginator

def review_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'review_list.html', {'page_obj': page_obj})


def review_list_api(request):
    page = int(request.GET.get('page', 1))
    per_page = 10
    reviews = Review.objects.all().order_by('-created_at')
    paginator = Paginator(reviews, per_page)
    page_obj = paginator.get_page(page)

    reviews_data = [
        {
            'username': review.user.username,
            'photo': review.user.profile_pic.url if review.user.profile_pic else '/static/images/default_avatar.png',
            'rating': review.rating,
            'text': review.text,
            'created_at': review.created_at.strftime('%B %d, %Y'),
        }
        for review in page_obj
    ]

    return JsonResponse({
        'reviews': reviews_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
    })