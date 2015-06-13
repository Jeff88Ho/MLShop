from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from rango.bing_search import run_query
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.auth.models import User



def category(request, category_name_slug):
    context_dict = {}

    context_dict['result_list'] = None
    context_dict['query'] = None

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

            context_dict['result_list'] = result_list
            context_dict['query'] = query

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        # creator_id = category.creator_id
        #
        # if creator_id == 0:
        #     context_dict['creator'] = "Cool Guy"
        #
        # else:
        #     user = User.objects.get(id=creator_id)
        #     context_dict['creator'] = user.username


        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category


    except Category.DoesNotExist:
        pass

    if not context_dict['query']:
        context_dict['query'] = category.name

    return render(request, 'rango/category.html', context_dict)





def index(request):

    category_list = Category.objects.order_by('-likes')[:100]
    page_list = Page.objects.order_by('-views')[:100]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')

    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 60:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits


    if visits:
        context_dict['visits'] = visits
    else:
        context_dict['visits'] = 0

    if last_visit:
        context_dict['last_visit'] = last_visit
    else:
        context_dict['last_visit'] = "No last visit info"


    response = render(request,'rango/index.html', context_dict)

    return response



def about(request):

    if request.session.get('visits'):
        visits = request.session.get('visits')
    else:
        visits = 0

    if request.session.get('last_visit'):
        last_visit = request.session.get('last_visit')
    else:
        last_visit = "No last visit info"


    response = render(request, 'rango/about.html', {'visits': visits, 'last_visit': last_visit})

    return response


def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            category = form.save(commit=False)


            creator = request.user
            category.creator = creator

            category.save()

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors

    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})


def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0

                provider = request.user
                page.provider = provider

                page.save()
                # probably better to use a redirect here.

                category_url = '/rango/category/%s' % category_name_slug

                return redirect(category_url)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form': form, 'category': cat,}

    return render(request, 'rango/add_page.html', context_dict)


def register(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered} )



def user_login(request):

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
                # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
                # because the request.POST.get('<variable>') returns None, if the value does not exist,
                # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html', {})


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')



def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


def track_url(request):

    url = '/rango/'

    if request.method == 'GET':


        if 'page_id' in request.GET:
            page_id = request.GET['page_id']

            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)




def register_profile(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    added_profile = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if profile_form.is_valid():
            # Save the user's form data to the database.

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.

            user = request.user

            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            added_profile = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
            'rango/add_profile.html',
            {'profile_form': profile_form, 'added_profile': added_profile} )




@login_required
def profile(request):

    context_dict = {}

    user = request.user

    user = User.objects.get(username=user)
    username = user.username
    userid = user.id

    profile = UserProfile.objects.get(user=userid)
    website = profile.website
    picture = profile.picture

    context_dict['username'] = username
    context_dict['userid'] = userid
    context_dict['website'] = website
    context_dict['picture'] = picture


    user_category_list = Category.objects.filter(creator=user)

    likes = 0
    for user_category in user_category_list:
        likes += user_category.likes



    user_page_list = Page.objects.filter(provider=user)

    views = 0
    for user_page in user_page_list:
        views += user_page.views


    context_dict['likes'] = likes
    context_dict['views'] = views

    response = render(request,'rango/profile.html',context_dict )

    return response


@login_required
def like_category(request):

    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['cat_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes =  likes
            cat.save()

    return HttpResponse(likes)


def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
            cat_list = Category.objects.filter(name__icontains=starts_with)

    if max_results > 0:
            if len(cat_list) > max_results:
                    cat_list = cat_list[:max_results]

    return cat_list


def suggest_category(request):

    cat_list = []

    starts_with = ''
    if request.method == 'GET':
            starts_with = request.GET['suggestion']

    cat_list = get_category_list(10, starts_with)

    return render(request, 'rango/search_cats.html', {'cats': cat_list})



def get_page_list(max_results=0, starts_with=''):
    page_list = []
    if starts_with:
            page_list = Page.objects.filter(title__icontains=starts_with)

    if max_results > 0:
            if len(page_list) > max_results:
                    page_list = page_list[:max_results]

    return page_list


def suggest_page(request):

    page_list = []

    starts_with = ''
    if request.method == 'GET':
            starts_with = request.GET['suggestion']

    page_list = get_page_list(10, starts_with)

    return render(request, 'rango/search_pages.html', {'pages': page_list})






@login_required
def auto_add_page(request):

    context = RequestContext(request)
    cat_id = None
    url = None
    title = None

    context_dict = {}

    if request.method == 'GET':
        cat_id = request.GET['cat_id']
        title = request.GET['title']
        url = request.GET['url']
        provider = request.user


        if cat_id:

            category = Category.objects.get(id=int(cat_id))

            p = Page.objects.get_or_create(category=category, title=title, url=url, provider=provider)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages

    return render(request, 'rango/page_list.html', context_dict)


def check_username(username=''):

    username_taken = False

    all_user_list = User.objects.filter(username=username)

    if all_user_list:
        username_taken = True

    return username_taken



def username_taken(request):

    username = ''
    if request.method == 'GET':
            username = request.GET['id_username']

    username_taken = check_username(username=username)

    email_taken = False

    return render(request, 'rango/username_taken.html', {'username_taken': username_taken, 'email_taken': email_taken})



def check_email(email=''):

    email_taken = False

    all_user_list = User.objects.filter(email=email)

    if all_user_list:
        email_taken = True

    return email_taken



def email_taken(request):

    email = ''
    if request.method == 'GET':
            email = request.GET['id_email']

    username_taken = False


    email_taken = check_email(email=email)

    return render(request, 'rango/username_taken.html', {'username_taken': username_taken, 'email_taken': email_taken})