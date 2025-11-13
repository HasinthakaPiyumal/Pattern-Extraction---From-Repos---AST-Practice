# Cluster 2

class URLHandler:
    """
    This class is used to handle the URLs
    """

    @staticmethod
    def is_valid_url(url):
        parsed_url = urlsplit(url)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)

    @staticmethod
    def extract_links(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(url, href)
                if URLHandler.is_valid_url(absolute_url):
                    links.append(absolute_url)
        return links

    @staticmethod
    def extract_links_from_websites(websites):
        all_links = []
        for website in websites:
            links = URLHandler.extract_links(website)
            all_links.extend(links)
        return all_links

@staticmethod
def extract_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(url, href)
            if URLHandler.is_valid_url(absolute_url):
                links.append(absolute_url)
    return links

class GoogleLoginView(APIView):
    """
    View for Google login.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            try:
                app = Application.objects.get(name='google')
            except Application.DoesNotExist:
                return Response({'error': 'OAuth2 Application not found.'}, status=status.HTTP_404_NOT_FOUND)
            try:
                access_token = app.accesstoken_set.get(user=user)
                refresh_token = RefreshToken.objects.get(user=user, access_token=access_token)
                context = {'access_token': access_token.token, 'refresh_token': refresh_token.token}
                return Response(context, status=status.HTTP_200_OK)
            except AccessToken.DoesNotExist:
                return Response({'error': 'Access token not found for the user.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return redirect(load_strategy().build_absolute_uri('/social-auth/login/google-oauth2/'))

def post(self, request, *args, **kwargs):
    user = request.user
    if user.is_authenticated:
        try:
            app = Application.objects.get(name='google')
        except Application.DoesNotExist:
            return Response({'error': 'OAuth2 Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            access_token = app.accesstoken_set.get(user=user)
            refresh_token = RefreshToken.objects.get(user=user, access_token=access_token)
            context = {'access_token': access_token.token, 'refresh_token': refresh_token.token}
            return Response(context, status=status.HTTP_200_OK)
        except AccessToken.DoesNotExist:
            return Response({'error': 'Access token not found for the user.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return redirect(load_strategy().build_absolute_uri('/social-auth/login/google-oauth2/'))

class EmailBackend(ModelBackend):
    """
    Authenticate using an e-mail address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
        if user.check_password(password):
            return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

def authenticate(self, request, username=None, password=None, **kwargs):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(email=username)
    except UserModel.DoesNotExist:
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None
    if user.check_password(password):
        return user

def get_user(self, user_id):
    UserModel = get_user_model()
    try:
        return UserModel.objects.get(pk=user_id)
    except UserModel.DoesNotExist:
        return None

